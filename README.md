# Amp
The Amp programming language, currently not incredibly useful, but new features are being implemented constantly.

## Goals
 - Compile to relatively fast machine code
 - Implement "comfort" features often found in interpreted languages
 - Be self hosted (compiler written in itself)
 - Useful for a variety of situations

Currently only supports linux, but it is designed to eventually be ported to other platforms like Windows, MacOS, and WebAssembly.

## Documentation
TBD (see **test** directory for some functional snippets of code)

## Running
To run one of the examples (only currently functional for linux):
```
python amp.py test/[test].lang -r
```
