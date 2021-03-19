# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Added
- #### Overall
  - This changelog.  Will document user relevant changes as well as intended changes in **Unreleased** section.
  - Added installation testing directly to setup.
    - Uses pytest, this should ensure program runs tests before completing installation.
  - Added 'library_layout' to config.
    - 'library_layout' can be automatically detected from an ISA file.

- #### DGE/Normalization
  - DGE checks
  - Setting output path for logs in CLI/Config. (Default: 'VV_output' in current working directory).
  - Setting overwrite toggle for logs in CLI/Config. (Default: False)

- #### STAR
  - MultiQC based checks

### Changed
- #### Overall
  - 'parameters' renamed to 'cutoffs'. This is to clarify their specific role in defining V&V flagging thresholds.
    - Includes renaming of params to cutoffs and parameter.py to cutoffs.py.
  - Clarity enhancing and typo fixing related changes to Main program help menu.
  - Clarity enhancing changes to the README.md
  - Moved the following values from cutoffs.py to config as they match the scope better 'hasERCC','middlePoint'.
    - Both can be automatically detected from an ISA file.
  - Improved config file comments to enhance clarity.
  - Log message now broken up into a series columns.
    - This should allow more fine-grain control to information overload in user-ready logs.
      - Columns added: 'full_path', 'relative_path', 'indices', 'entity_value', 'max_thresholds', 'min_thresholds', 'outlier_thresholds', 'debug_message', 'unique_critera_results'
      - Column removed: 'message' (information now split into new columns)
- #### Raw Reads [Fastq.gz]
  - 'fastq_lines_to_check' cutoff changed to 'fastq_proportion_to_check'.
    - Uses seqtk to perform proportion based subsampling.

- #### Trimmed Reads [Fastq.gz]
  - 'fastq_lines_to_check' cutoff changed to 'fastq_proportion_to_check'.
    - Uses seqtk to perform proportion based subsampling.

### Fixed
  - "UnboundLocalError: local variable 'flagged' referenced before assignment" bug in Raw Reads [MultiQC]

### Removed
  - Timestamped intermediate log directories

## [0.1.2] - 2021-03-17
- First pre-release tracked on Github
