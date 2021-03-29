# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Added
- #### STAR
  - MultiQC based checks

### Changed
  - Moved the following values from cutoffs.py to samplesheet as they match the scope better 'middlePoint'.

- #### Raw Reads [Fastq.gz]
  - 'fastq_lines_to_check' cutoff changed to 'fastq_proportion_to_check'.
    - Uses seqtk to perform proportion based subsampling.

- #### Trimmed Reads [Fastq.gz]
  - 'fastq_lines_to_check' cutoff changed to 'fastq_proportion_to_check'.
    - Uses seqtk to perform proportion based subsampling.

### Fixed

### Removed

## [0.3.0] - 2021-03-26
### Added
  - Setting output path for logs in CLI. (Default: 'VV_Log/VV_log.tsv' in current working directory).
  - Setting data path for in CLI/Config. (Default: current working directory).
  - Setting overwrite toggle for logs in CLI. (Default: False)

### Changed
- #### Overall
  - RNASeq_Samplesheet replaces most of the configuration found in config.
  - Remaining config for halt severity level and parent data directory (the one holding the raw and processed data) moved to CLI args with default halt severity level set to 90 and default parent data directory set to current working directory.

### Removed
  - Config file, replaced by RNASeq_Samplesheet.csv file and CLI args.
  - Timestamped intermediate log directories

## [0.2.0] - 2021-03-23
### Added
- #### DGE/Normalization
  - DGE checks (D_0005 through D_0012)

### Changed
- #### Overall
  - Clarity enhancing and typo fixing related changes to Main program help menu.
  - Clarity enhancing changes to the README.md
  - 'parameters' renamed to 'cutoffs'. This is to clarify their specific role in defining V&V flagging thresholds.
    - Includes renaming of params to cutoffs and parameter.py to cutoffs.py.
  - Log message now broken up into a series columns.
    - This should allow more fine-grain control to information overload in user-ready logs.
      - Columns added: 'full_path', 'relative_path', 'indices', 'entity_value', 'max_thresholds', 'min_thresholds', 'outlier_thresholds', 'debug_message', 'unique_critera_results'
      - Column removed: 'message' (information now split into new columns)
### Fixed
  - "UnboundLocalError: local variable 'flagged' referenced before assignment" bug in Raw Reads [MultiQC]

## [0.1.3] - 2021-03-19
### Added
  - This changelog.  Will document user relevant changes as well as intended changes in **Unreleased** section.
  - Added installation testing directly to setup.
    - Uses pytest, this should ensure program runs tests before completing installation.

## [0.1.2] - 2021-03-17
- First pre-release tracked on Github

[0.1.3]: https://github.com/J-81/JDO_V-V/compare/0.1.2...0.1.3
