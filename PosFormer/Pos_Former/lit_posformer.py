import zipfile
from typing import List , Tuple
import time
import torch
import pytorch_lightning as pl
import torch.optim as optim
from torch import FloatTensor, LongTensor

from Pos_Former.datamodule import Batch, vocab ,label_make_muti
from Pos_Former.model.posformer import PosFormer
from Pos_Former.utils.utils import (ExpRateRecorder, Hypothesis,ce_loss_all,ce_loss,
                               to_bi_tgt_out)

class LitPosFormer(pl.LightningModule):
    def __init__(
        self,
        d_model: int,
        # encoder
        growth_rate: int,
        num_layers: int,
        # decoder
        nhead: int,
        num_decoder_layers: int,
        dim_feedforward: int,
        dropout: float,
        dc: int,
        cross_coverage: bool,
        self_coverage: bool,
        # beam search
        beam_size: int,
        max_len: int,
        alpha: float,
        early_stopping: bool,
        temperature: float,
        # training
        learning_rate: float,
        patience: int,
    ):
        super().__init__()
        self.save_hyperparameters()

        self.model = PosFormer(
            d_model=d_model,
            growth_rate=growth_rate,
            num_layers=num_layers,
            nhead=nhead,
            num_decoder_layers=num_decoder_layers,
            dim_feedforward=dim_feedforward,
            dropout=dropout,
            dc=dc,
            cross_coverage=cross_coverage,
            self_coverage=self_coverage,
        )
        self.exprate_recorder = ExpRateRecorder()
        self.test_outputs = []

    def forward(
        self, img: FloatTensor, img_mask: LongTensor, tgt: LongTensor, logger
    ) -> Tuple[FloatTensor,FloatTensor]:
        """run img and bi-tgt

        Parameters
        ----------
        img : FloatTensor
            [b, 1, h, w]
        img_mask: LongTensor
            [b, h, w]
        tgt : LongTensor
            [2b, l]

        Returns
        -------
        FloatTensor
            [2b, l, vocab_size]
        """
        return self.model(img, img_mask, tgt, logger)

    def training_step(self, batch: Batch, _):      
        tgt, out = to_bi_tgt_out(batch.indices, self.device)
        out_hat , out_hat_layer ,out_hat_pos = self(batch.imgs, batch.mask, tgt , self.trainer.logger)
        tgt_list=tgt.cpu().numpy().tolist()
        layer_num , final_pos=label_make_muti.out2layernum_and_pos(tgt_list)
        layer_num_tensor=torch.LongTensor(layer_num)   #[2b,l,5]
        final_pos_tensor=torch.LongTensor(final_pos)   #[2b,l,6]
        layer_num_tensor=layer_num_tensor.cuda()
        final_pos_tensor=final_pos_tensor.cuda()  
        loss, layer_loss, pos_loss  = ce_loss_all(out_hat, out,out_hat_layer,layer_num_tensor,out_hat_pos,final_pos_tensor)
        self.log("train_loss", loss, logger=True, on_step=False, on_epoch=True, sync_dist=True,prog_bar=True)
        self.log("train_loss_pos",pos_loss, logger=True, on_step=False, on_epoch=True,prog_bar=True, sync_dist=True)
        self.log("train_loss_layernum",layer_loss, logger=True,on_step=False, on_epoch=True, sync_dist=True,prog_bar=True)
        loss = (loss+0.25*layer_loss+0.25*pos_loss)/1.5
        return loss

    def validation_step(self, batch: Batch, _):
        tgt, out = to_bi_tgt_out(batch.indices, self.device)
        out_hat , out_hat_layer ,out_hat_pos = self(batch.imgs, batch.mask, tgt,self.trainer.logger)
        
        tgt_list=tgt.cpu().numpy().tolist()
        layer_num , final_pos=label_make_muti.out2layernum_and_pos(tgt_list)
        layer_num_tensor=torch.LongTensor(layer_num)   #[2b,l,5]
        final_pos_tensor=torch.LongTensor(final_pos)   #[2b,l,6]
        layer_num_tensor=layer_num_tensor.cuda()
        final_pos_tensor=final_pos_tensor.cuda()  
        
        loss,layer_loss,pos_loss  = ce_loss_all(out_hat, out,out_hat_layer,layer_num_tensor,out_hat_pos,final_pos_tensor)

        self.log(
            "val_loss",
            loss,
            logger=True,
            on_step=False,
            on_epoch=True,
            prog_bar=True,
            sync_dist=True,
        )
        self.log(
            "val_loss_pos",
            pos_loss,
            logger=True,
            on_step=False,
            on_epoch=True,
            prog_bar=True,
            sync_dist=True,
        )
        self.log(
            "val_loss_layernum",
            layer_loss,
            logger=True,
            on_step=False,
            on_epoch=True,
            prog_bar=True,
            sync_dist=True,
        )
        hyps = self.approximate_joint_search(batch.imgs, batch.mask)

        self.exprate_recorder([h.seq for h in hyps], batch.indices)
        self.log(
            "val_ExpRate",
            self.exprate_recorder,
            logger=True,
            prog_bar=True,
            on_step=False,
            on_epoch=True,
        )

    def on_test_epoch_start(self):
        self.test_outputs = []


    def test_step(self, batch: Batch, _):
        # Sincronizamos CUDA para medir mejor el tiempo real
        if torch.cuda.is_available():
            torch.cuda.synchronize()

        start_time = time.time()

        hyps = self.approximate_joint_search(batch.imgs, batch.mask)

        if torch.cuda.is_available():
            torch.cuda.synchronize()

        inference_time = time.time() - start_time

        self.exprate_recorder(
            [h.seq for h in hyps],
            batch.indices
        )

        self.log(
            "batch_inference_time",
            inference_time
        )

        output = (
            batch.img_bases,
            [vocab.indices2label(h.seq) for h in hyps],
            inference_time,
        )

        self.test_outputs.append(output)

        return output


    def on_test_epoch_end(self):
        total_inference_time = sum(
        output[2] for output in self.test_outputs
        )

        print(f"Total Inference Time: {total_inference_time} seconds")

        exprate = self.exprate_recorder.compute()
        print(f"Validation ExpRate: {exprate}")

        with zipfile.ZipFile("result.zip", "w") as zip_f:
            for img_bases, preds, _ in self.test_outputs:
                for img_base, pred in zip(img_bases, preds):
                    content = f"%{img_base}\n${pred}$".encode()

                    with zip_f.open(
                        f"{img_base}.txt",
                        "w"
                    ) as f:
                        f.write(content)

        self.test_outputs.clear()
    def approximate_joint_search(
        self, img: FloatTensor, mask: LongTensor
    ) -> List[Hypothesis]:
        return self.model.beam_search(img, mask, **self.hparams)

    def configure_optimizers(self):
        optimizer = optim.SGD(
            self.parameters(),
            lr=self.hparams.learning_rate,
            momentum=0.9,
            weight_decay=1e-4,
        )
        
        reduce_scheduler = optim.lr_scheduler.ReduceLROnPlateau(
            optimizer,
            mode="max",
            factor=0.25,
            patience=self.hparams.patience // self.trainer.check_val_every_n_epoch,
        )
        scheduler = {
            "scheduler": reduce_scheduler,
            "monitor": "val_ExpRate",
            "interval": "epoch",
            "frequency": self.trainer.check_val_every_n_epoch,
            "strict": True,
        }
        
        return {"optimizer": optimizer, "lr_scheduler": scheduler}
