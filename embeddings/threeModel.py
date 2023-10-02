
import torch
from speechbrain.pretrained import Pretrained

from speechbrain.processing.features import Filterbank, spectral_magnitude

class MySTFT(torch.nn.Module):
    def __init__(
        self,
        sample_rate,
        win_length=25,
        hop_length=10,
        n_fft=400,
        window_fn=torch.hamming_window,
        normalized_stft=False,
        center=True,
        pad_mode="constant",
        onesided=True,
    ):
        super().__init__()
        self.sample_rate = sample_rate
        self.win_length = win_length
        self.hop_length = hop_length
        self.n_fft = n_fft
        self.normalized_stft = normalized_stft
        self.center = center
        self.pad_mode = pad_mode
        self.onesided = onesided

        # Convert win_length and hop_length from ms to samples
        self.win_length = int(
            round((self.sample_rate / 1000.0) * self.win_length)
        )
        self.hop_length = int(
            round((self.sample_rate / 1000.0) * self.hop_length)
        )

        self.window = window_fn(self.win_length)


    def forward(self, x):
        """Returns the STFT generated from the input waveforms.

        Arguments
        ---------
        x : tensor
            A batch of audio signals to transform.
        """

        stft = torch.stft(
            x,
            self.n_fft,
            self.hop_length,
            self.win_length,
            self.window.to(x.device),
            self.center,
            self.pad_mode,
            self.normalized_stft,
            self.onesided,
            return_complex=False,
        )

        # Retrieving the original dimensionality (batch,time, channels)
        stft = stft.transpose(2, 1)

        return stft


class FBankModel(torch.nn.Module):
    def __init__(self):
        super().__init__()
    def forward(self, x):
        features = spectral_magnitude(x)
        compute_fbanks = Filterbank(n_mels=80)
        feats = compute_fbanks(features)
        return feats

class FeatureModel(Pretrained):
    MODULES_NEEDED = [
        "compute_features",
        "mean_var_norm",
        "embedding_model",
        "classifier",
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def encode_batch(self, wavs, wav_lens=None, normalize=False ):
        """Encodes the input audio into a single vector embedding.

        The waveforms should already be in the model's desired format.
        You can call:
        ``normalized = <this>.normalizer(signal, sample_rate)``
        to get a correctly converted signal in most cases.

        Arguments
        ---------
        wavs : torch.Tensor
            Batch of waveforms [batch, time, channels] or [batch, time]
            depending on the model. Make sure the sample rate is fs=16000 Hz.
        wav_lens : torch.Tensor
            Lengths of the waveforms relative to the longest one in the
            batch, tensor of shape [batch]. The longest one should have
            relative length 1.0 and others len(waveform) / max_length.
            Used for ignoring padding.
        normalize : bool
            If True, it normalizes the embeddings with the statistics
            contained in mean_var_norm_emb.

        Returns
        -------
        torch.Tensor
            The encoded batch
        """
        # Storing waveform in the specified device
        wavs = wavs.to(self.device)
        wavs = wavs.float()

        # Computing features and embeddings
        self.mods.to( self.device )
        from speechbrain.processing.features import Filterbank, STFT
        from speechbrain.processing.features import spectral_magnitude
        compute_STFT = STFT(sample_rate=16000, win_length=25, hop_length=10, n_fft=400)
        features = compute_STFT(wavs)
        features = spectral_magnitude(features)
        compute_fbanks = Filterbank(n_mels=80)
        feats = compute_fbanks(features)
        #feats = self.mods.compute_features(wavs)
        return feats

    def forward(self, wavs, wav_lens=None):
        """Runs the classification"""
        # LIYI
        #return self.classify_batch(wavs, wav_lens)
        return self.encode_batch(wavs, wav_lens)
        #feats = wavs
        #return self.mods.embedding_model(feats, wav_lens)

class MyEmbedding0(Pretrained):
    """A ready-to-use class for utterance-level classification (e.g, speaker-id,
    language-id, emotion recognition, keyword spotting, etc).

    The class assumes that an encoder called "embedding_model" and a model
    called "classifier" are defined in the yaml file. If you want to
    convert the predicted index into a corresponding text label, please
    provide the path of the label_encoder in a variable called 'lab_encoder_file'
    within the yaml.

    The class can be used either to run only the encoder (encode_batch()) to
    extract embeddings or to run a classification step (classify_batch()).
    ```

    Example
    -------
    >>> import torchaudio
    >>> from speechbrain.pretrained import EncoderClassifier
    >>> # Model is downloaded from the speechbrain HuggingFace repo
    >>> tmpdir = getfixture("tmpdir")
    >>> classifier = EncoderClassifier.from_hparams(
    ...     source="speechbrain/spkrec-ecapa-voxceleb",
    ...     savedir=tmpdir,
    ... )

    >>> # Compute embeddings
    >>> signal, fs = torchaudio.load("tests/samples/single-mic/example1.wav")
    >>> embeddings = classifier.encode_batch(signal)

    >>> # Classification
    >>> prediction = classifier.classify_batch(signal)
    """

    MODULES_NEEDED = [
        "compute_features",
        "embedding_model",
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def encode_batch(self, stft_out, wav_lens=None, normalize=False):
        """Encodes the input audio into a single vector embedding.

        The waveforms should already be in the model's desired format.
        You can call:
        ``normalized = <this>.normalizer(signal, sample_rate)``
        to get a correctly converted signal in most cases.

        Arguments
        ---------
        wavs : torch.Tensor
            Batch of waveforms [batch, time, channels] or [batch, time]
            depending on the model. Make sure the sample rate is fs=16000 Hz.
        wav_lens : torch.Tensor
            Lengths of the waveforms relative to the longest one in the
            batch, tensor of shape [batch]. The longest one should have
            relative length 1.0 and others len(waveform) / max_length.
            Used for ignoring padding.
        normalize : bool
            If True, it normalizes the embeddings with the statistics
            contained in mean_var_norm_emb.

        Returns
        -------
        torch.Tensor
            The encoded batch
        """

        # Storing waveform in the specified device
        wav_lens = wav_lens.to(self.device)

        features = spectral_magnitude(stft_out)
        compute_fbanks = Filterbank(n_mels=80)
        feats = compute_fbanks(features)

        # Computing features and embeddings
        self.mods.to( self.device )
        #feats = self.mods.mean_var_norm(feats, wav_lens)
        mn = MyNormalization()
        feats = mn.forward( feats, wav_lens )
        embeddings = self.mods.embedding_model(feats, wav_lens)
        if normalize:
            embeddings = self.hparams.mean_var_norm_emb(
                #embeddings, torch.ones(embeddings.shape[0], device=self.device)
                embeddings, torch.ones(embeddings.size(0), device=self.device)
            )
        return embeddings

    def forward(self, stft_out, wav_lens):
        """Runs the classification"""
        # LIYI
        return self.encode_batch(stft_out, wav_lens)


class EMDModel(Pretrained):
    MODULES_NEEDED = [
        "compute_features",
        "mean_var_norm",
        "embedding_model",
        "classifier",
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def encode_batch(self, feats, wav_lens=None):
        """Encodes the input audio into a single vector embedding.

        The waveforms should already be in the model's desired format.
        You can call:
        ``normalized = <this>.normalizer(signal, sample_rate)``
        to get a correctly converted signal in most cases.

        Arguments
        ---------
        wavs : torch.Tensor
            Batch of waveforms [batch, time, channels] or [batch, time]
            depending on the model. Make sure the sample rate is fs=16000 Hz.
        wav_lens : torch.Tensor
            Lengths of the waveforms relative to the longest one in the
            batch, tensor of shape [batch]. The longest one should have
            relative length 1.0 and others len(waveform) / max_length.
            Used for ignoring padding.
        normalize : bool
            If True, it normalizes the embeddings with the statistics
            contained in mean_var_norm_emb.

        Returns
        -------
        torch.Tensor
            The encoded batch
        """
        # Assign full length if wav_lens is not assigned
        if wav_lens is None:
            #wav_lens = torch.ones(wavs.shape[0], device=self.device)
            wav_lens = torch.ones(feats.size(0), device=self.device)

        # Storing waveform in the specified device
        feats, wav_lens = feats.to(self.device), wav_lens.to(self.device)
        feats = feats.float()

        mn = MyNormalization()
        feats = mn.forward( feats, wav_lens )
        self.mods.to( self.device )
        embeddings = self.mods.embedding_model(feats, wav_lens)
        return embeddings

    def forward(self, feats, wav_lens):
        """Runs the classification"""
        return self.encode_batch(feats, wav_lens)

class MyNormalization:
    """Performs mean and variance normalization of the input tensor.

    Arguments
    ---------
    mean_norm : True
         If True, the mean will be normalized.
    std_norm : True
         If True, the standard deviation will be normalized.
    norm_type : str
         It defines how the statistics are computed ('sentence' computes them
         at sentence level, 'batch' at batch level, 'speaker' at speaker
         level, while global computes a single normalization vector for all
         the sentences in the dataset). Speaker and global statistics are
         computed with a moving average approach.
    avg_factor : float
         It can be used to manually set the weighting factor between
         current statistics and accumulated ones.

    Example
    -------
    >>> import torch
    >>> norm = InputNormalization()
    >>> inputs = torch.randn([10, 101, 20])
    >>> inp_len = torch.ones([10])
    >>> features = norm(inputs, inp_len)
    """


    def __init__(
        self,
        mean_norm=True,
        std_norm=False,
        norm_type="sentence",
    ):
        super().__init__()
        self.mean_norm = mean_norm
        self.std_norm = std_norm
        self.norm_type = norm_type
        self.eps = 1e-10

    def forward(self, x, lengths):
        """Returns the tensor with the surrounding context.

        Arguments
        ---------
        x : tensor
            A batch of tensors.
        lengths : tensor
            A batch of tensors containing the relative length of each
            sentence (e.g, [0.7, 0.9, 1.0]). It is used to avoid
            computing stats on zero-padded steps.
        spk_ids : tensor containing the ids of each speaker (e.g, [0 10 6]).
            It is used to perform per-speaker normalization when
            norm_type='speaker'.
        """
        #N_batches = x.shape[0]
        N_batches = x.size(0)
        seq_len = x.size(1)

        for snt_id in range(N_batches):

            # Avoiding padded time steps
            # Changed to int64, otherwise go error:
            # Type parameter (Tind) of Optype (Slice) bound to different types (tensor(int64) and tensor(int32) in node (/Slice)
            #actual_size = torch.round(lengths[snt_id] * x.shape[1]).long()
            actual_size = torch.round(lengths[snt_id] * seq_len).long()

            # computing statistics
            current_mean, current_std = self._compute_current_stats(
                x[snt_id, 0:actual_size, ...]
            )

            if self.norm_type == "sentence":
                x[snt_id] = (x[snt_id] - current_mean) / current_std


        return x

    def _compute_current_stats(self, x):
        """Returns the tensor with the surrounding context.

        Arguments
        ---------
        x : tensor
            A batch of tensors.
        """
        # Compute current mean
        if self.mean_norm:
            current_mean = torch.mean(x, dim=0).detach()
        else:
            current_mean = torch.tensor([0.0], device=x.device)

        # Compute current std
        if self.std_norm:
            current_std = torch.std(x, dim=0).detach()
        else:
            current_std = torch.tensor([1.0], device=x.device)

        # Improving numerical stability of std
        current_std = torch.max(
            current_std, self.eps * torch.ones_like(current_std)
        )

        return current_mean, current_std
