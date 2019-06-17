from utils import *

class embed(nn.Module):
    def __init__(self, char_vocab_size, word_vocab_size, embed_size):
        super().__init__()
        dim = embed_size // len(EMBED) # dimension of each embedding vector

        # architecture
        if "char-cnn" in EMBED:
            self.char_embed = embed_cnn(char_vocab_size, dim)
        if "lookup" in EMBED:
            self.word_embed = nn.Embedding(word_vocab_size, dim, padding_idx = PAD_IDX)

    def forward(self, xc, xw):
        hc = self.char_embed(xc) if "char-cnn" in EMBED else None
        hw = self.word_embed(xw) if "lookup" in EMBED else None
        h = torch.cat([h for h in [hc, hw] if type(h) == torch.Tensor], 2)
        return h

class embed_cnn(nn.Module):
    def __init__(self, dim_in, dim_out):
        super().__init__()
        self.embed_size = 50
        self.num_featmaps = 50 # feature maps generated by each kernel
        self.kernel_sizes = [3]

        # architecture
        self.embed = nn.Embedding(dim_in, self.embed_size, padding_idx = PAD_IDX)
        self.conv = nn.ModuleList([nn.Conv2d(
            in_channels = 1, # Ci
            out_channels = self.num_featmaps, # Co
            kernel_size = (i, self.embed_size) # (height, width)
        ) for i in self.kernel_sizes]) # num_kernels (K)
        self.dropout = nn.Dropout(DROPOUT)
        self.fc = nn.Linear(len(self.kernel_sizes) * self.num_featmaps, dim_out)

    def forward(self, x):
        x = x.view(-1, x.size(2)) # [batch_size (B) * word_seq_len (L), char_seq_len (H)]
        x = self.embed(x) # [B * L, H, embed_size (W)]
        x = x.unsqueeze(1) # [B * L, Ci, H, W]
        h = [conv(x) for conv in self.conv] # [B * L, Co, H, 1] * K
        h = [F.relu(k).squeeze(3) for k in h] # [B * L, Co, H] * K
        h = [F.max_pool1d(k, k.size(2)).squeeze(2) for k in h] # [B * L, Co] * K
        h = torch.cat(h, 1) # [B * L, Co * K]
        h = self.dropout(h)
        h = self.fc(h) # [B * L, dim_out]
        h = h.view(BATCH_SIZE, -1, h.size(1)) # [B, L, dim_out]
        return h
