# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
- Add possibility of embedding ttf and unicode fonts.

## [0.4.9] - 2022-02-18
### Changed
- Improved how group elements work, with "min_height" and "shrink" style
  properties.
### Fixed
- Fixed error with margins of elements in content boxes.

## [0.4.8] - 2022-02-12
### Added
- Added support for png images embedding.
- Added per page running sections and styles.
### Fixed
- Added "min_height" style property to make the images downsize to min height
  when they don't fit in the available height.

## [0.4.7] - 2022-02-10
### Added
- Added group elements.
- Added per page running sections.
### Fixed
- Fixed some typos in the docs.

## [0.4.6] - 2021-11-11
### Fixed
- Fixed issue found in table module.

## [0.4.5] - 2021-10-04
### Fixed
- Fixed issue #10 related with error with hexagesimal colors.

## [0.4.4] - 2021-08-18
### Added
- Numbers in paragraph parts are now converted to strings. PR #9

## [0.4.3] - 2021-08-18
### Added
- Fixed issues #7 related with incomplete borders when combining cells.

## [0.4.2] - 2021-08-18
### Fixed
- Fixed issues #3 and #5 related with footnotes and incomplete sections.

## [0.4.1] - 2021-07-26
### Fixed
- An alternative for deepcopy was created, and some modifications were made in 
  the rest of the code to replace deepcopy with our alternative. Some simple
  time measurements were made and this fix has improved the speed of content
  module 8 to 10 times.

## [0.4.0] - 2021-07-19
### Added
- `page_style` properties, in `document` module are now defined inside `style`
  key.

## [0.3.0] - 2021-07-16
### Added
- PDF Outlines are now available.