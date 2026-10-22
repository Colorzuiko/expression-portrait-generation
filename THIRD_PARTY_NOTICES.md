# Included runtime components

- `scripts/image-matting.cjs` is maintained from the user's Deback CLI. The foreground-preserving revision disables default alpha contraction, limits despill to contaminated pixels, and adds foreground QA. The original Deback file is not modified. Its bundled Commander.js code uses the MIT license; the notice is retained in `scripts/licenses/commander-LICENSE`. Upstream notice: https://github.com/tj/commander.js/blob/master/LICENSE
- `sharp` is a runtime dependency installed by `npm ci`, locked in `package-lock.json`. Its package and native dependencies retain their own license files when installed. Platform-specific `node_modules` binaries are not redistributed in this share archive.

The project code and skill documentation are licensed under the root MIT LICENSE. Bundled third-party code retains its own notices. No character reference images or generated portrait packs are included; their rights are not granted by this project license.
