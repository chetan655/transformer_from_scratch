import torch
import torch.nn as nn
from torch.utils.data import Dataset
from typing import Any

'''
    working of BiligualDataset :- 
        
'''

class BiligualDataset(Dataset):
    def __init__(self, ds, tokenizer_src, tokenizer_tgt, src_lang, tgt_lang, seq_len) -> None:
        super().__init__()
        self.ds = ds
        self.tokenizer_src = tokenizer_src
        self.tokenizer_tgt = tokenizer_tgt
        self.src_lang = src_lang
        self.tgt_lang = tgt_lang
        self.seq_len = seq_len

        self.sos_token = torch.tensor([tokenizer_tgt.token_to_id("[SOS]")], dtype=torch.int64)  # it returns its toke
        self.eos_token = torch.tensor([tokenizer_tgt.token_to_id("[EOS]")], dtype=torch.int64)
        self.pad_token = torch.tensor([tokenizer_tgt.token_to_id("[PAD]")], dtype=torch.int64)

    def __len__(self):
        return len(self.ds)   # returns length by counting all the items in ds
    
    def __getitem__(self, index: Any) -> Any:
        src_target_pair = self.ds[index]
        src_text = src_target_pair['translation'][self.src_lang]      # extract the src and tgt language from the dataset
        tgt_text = src_target_pair['translation'][self.tgt_lang]

        enc_input_tokens = self.tokenizer_src.encode(src_text).ids    # ecoder(src_text) -> this method takes a str and converts it into a Encoding object. this object things like ids, tokens
        # dec_input_tokens = self.tokenizer_tgt(tgt_text).ids
        dec_input_tokens = self.tokenizer_tgt.encode(tgt_text).ids


        enc_num_padding_tokens = self.seq_len - len(enc_input_tokens) - 2  # (2? -> one for SOS, one for EOS)
        dec_num_padding_tokens = self.seq_len - len(dec_input_tokens) - 1  # (1? -> for SOS, decoder have to predict EOS)

        if enc_num_padding_tokens < 0 or dec_num_padding_tokens < 0:
            raise ValueError('sentence is too long.')                                                                                                                                          
        
        # add sos and eos to the source text
        encoder_input = torch.cat(
            [
                self.sos_token,
                torch.tensor(enc_input_tokens, dtype=torch.int64),
                self.eos_token,
                torch.tensor([self.pad_token] * enc_num_padding_tokens, dtype=torch.int64)
            ]
        )

        # add sos to the decoder input
        decoder_input = torch.cat(
            [
                self.sos_token,
                torch.tensor(dec_input_tokens, dtype=torch.int64),
                torch.tensor([self.pad_token] * dec_num_padding_tokens, dtype=torch.int64)
            ]
        )

        # add eos to the label
        label = torch.cat(
            [
                torch.tensor(dec_input_tokens, dtype=torch.int64),
                self.eos_token,
                torch.tensor([self.pad_token] * dec_num_padding_tokens, dtype=torch.int64)
            ]
        )

        assert encoder_input.size(0) == self.seq_len
        assert decoder_input.size(0) == self.seq_len
        assert label.size(0) == self.seq_len

        return {
            "encoder_input": encoder_input,  # seq_len
            "decoder_input": decoder_input,   # seq_len
            "encoder_mask": (encoder_input != self.pad_token).unsqueeze(0).unsqueeze(0).int(),  # [1,1,seq_len]
            "decoder_mask": (decoder_input != self.pad_token).unsqueeze(0).unsqueeze(0).int() & causal_mask(decoder_input.size(0)),  # (1, 1, seq_len) & (1, seq_len, seq_len)
            "label": label,   # (seq_len)
            "src_text": src_text,
            "tgt_text": tgt_text
        }
    
def causal_mask(size):
    mask = torch.triu(torch.ones(1, size, size), diagonal=1).type(torch.int64)       # this is built-in method in pytorch to make a matrix that is diagonally half 0 and other half 1
    return mask == 0                                                               # it will convert 1 to True and 0 to False



