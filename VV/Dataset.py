class Dataset():
    def __init__(self,
                 accession: str,
                 fromGenelab: bool,
                 samples: list):
        self.accession = accession
        self.fromGenelab = fromGenelab
        self.samples = samples

class RNASeq_Dataset(Dataset):
    def __init__(self,
                 library_layout: str,
                 **kwargs):
        super().__init__(**kwargs)

        ALLOWED_LAYOUTS = {"single","paired_end"}

        if library_layout in ALLOWED_LAYOUTS:
            self.library_layout = library_layout
        else:
            raise ValueError(f"Library layout must be from {ALLOWED_LAYOUTS}")
