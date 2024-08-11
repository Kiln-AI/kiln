# MacOS Code Signing

How to sign on of the builds from GitHub Actions for offical release.

Easy way, but just signs with personal ID, not developer ID: `codesign --force --deep -s - fune.app`

Proper way with a developer ID:

1. Get developer ID name: `security find-identity -v -p codesigning`
2. Run `codesign --force --deep -s "Developer ID Application: YOUR NAME (XXXXXXXX)" fune.app`
