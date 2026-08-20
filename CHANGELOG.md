# Changelog

Maintained by [release-please](https://github.com/googleapis/release-please)
from conventional commit messages. Do not edit by hand.

## [0.2.0](https://github.com/Alberto-Codes/saucier/compare/v0.1.0...v0.2.0) (2026-08-20)


### ⚠ BREAKING CHANGES

* **extraction:** `resolve_parent` takes a mapping of candidates rather than the mother set, and a recorded `parent` may be any catalogued concept rather than a mother concept.

### Features

* **extraction:** resolve a parent to any catalogued preparation ([5ac256c](https://github.com/Alberto-Codes/saucier/commit/5ac256c31ed83d6f295eca4b3793fdb209816a9c))


### Fixes

* **extraction:** bind a mother to its own entry, not its shortest alias ([590c312](https://github.com/Alberto-Codes/saucier/commit/590c3128004f375aeea147d7d2b7126bcb46f58a))


### Documentation

* **readme:** link the rendered site rather than raw markdown ([ce7b04f](https://github.com/Alberto-Codes/saucier/commit/ce7b04f7156f40caad9a27605fc404093cf7643b))

## [0.1.0](https://github.com/Alberto-Codes/saucier/compare/v0.0.1...v0.1.0) (2026-08-20)


### ⚠ BREAKING CHANGES

* **extraction:** `SourceText` implementations must provide `line_offset`. `CatalogueStore.save` returns the destination. `Term.of` is removed, `SourceRef` is keyword-only, and `Preparation.parent` has no default. Recorded line numbers changed by the licence header offset.

### Features

* **ci:** cut releases as drafts, with a pre-flight checklist ([a8a7272](https://github.com/Alberto-Codes/saucier/commit/a8a72722b353696e29486477f19e36ef003aa13d))
* **docs:** cite the source and the language standard ([c24ddf0](https://github.com/Alberto-Codes/saucier/commit/c24ddf05f93962c9e61354df878e2939cb9df6c4))
* **docs:** draw the pipeline and the release flow ([57d9d21](https://github.com/Alberto-Codes/saucier/commit/57d9d216e174759b250967532aa3c1c088b17509))
* **docs:** give the site a frame that later pages inherit ([935ce8e](https://github.com/Alberto-Codes/saucier/commit/935ce8e47d51d8279de9d3c94e41a2e690b20bed))
* **docs:** publish the site to GitHub Pages from the docstrings ([cff3d1f](https://github.com/Alberto-Codes/saucier/commit/cff3d1f4bccee136f12f178d9ac8294160b8884f))
* **docs:** rebuild the site around the citation, not the hero ([5f22281](https://github.com/Alberto-Codes/saucier/commit/5f22281f740c253724cb649dd2200b1fbfbe4a1c))
* **gates:** enforce the glossary and the writing system ([27cf0f9](https://github.com/Alberto-Codes/saucier/commit/27cf0f931efb57862160df1cc3fc12845c8a2583))
* **v01:** read Escoffier into a traceable sauce catalogue ([555ff5e](https://github.com/Alberto-Codes/saucier/commit/555ff5ef948d8425ecfd62de153e3de581480c9b))


### Fixes

* **ci:** answer the CodeQL findings, and stop one from recurring ([d3b6847](https://github.com/Alberto-Codes/saucier/commit/d3b6847150e07522f7d6d0fc972596795a383e2e))
* **ci:** keep every recorded version in step through a release ([bea908c](https://github.com/Alberto-Codes/saucier/commit/bea908cb5191d7dd1f0c7fa01c82489ac62651f0))
* **ci:** make the docvet gate check files ([c46dc3b](https://github.com/Alberto-Codes/saucier/commit/c46dc3b37985f46e325fb83e8c9ea2815189ad84))
* **ci:** replace uv-secure with the audit built into uv ([ae52b40](https://github.com/Alberto-Codes/saucier/commit/ae52b4048b02b53cad94215c0ea17ccdd0845727))
* **docs:** correct the release diagram and gate the published counts ([81a23a0](https://github.com/Alberto-Codes/saucier/commit/81a23a0e9d855e3d23c2ab951754f4d74b2b8268))
* **docs:** render mermaid on the site too ([3f8e4cc](https://github.com/Alberto-Codes/saucier/commit/3f8e4cc0e0d8c5d2f1e0706538629e7729cfc9f4))
* **extraction:** read what counts as a sauce from the source ([06d43b8](https://github.com/Alberto-Codes/saucier/commit/06d43b8b6674f42e613e2540e3394b7b648247ba))
* **gates:** stop the gate scripts reporting success on nothing ([6330c18](https://github.com/Alberto-Codes/saucier/commit/6330c180721160a51aa59dad4f80887a1956fe7c))
* **repo:** base the ignore file on the canonical Python template ([72249fd](https://github.com/Alberto-Codes/saucier/commit/72249fda3590b15ffbc0e743f7992af2cf10f2f5))
* **repo:** stop tracking the coverage database ([8436b74](https://github.com/Alberto-Codes/saucier/commit/8436b747da1c205b0d8e6c4e9544b3385062b5b2))


### Documentation

* **adr:** cite the projects ADR-0001 weighs ([2da725d](https://github.com/Alberto-Codes/saucier/commit/2da725dfffcef606f92dfe25be5367510a271d35))
* **adr:** record the decisions an agent would confidently reverse ([75d2f60](https://github.com/Alberto-Codes/saucier/commit/75d2f60de3dac1676d0f514aea777ea1524e27a2))
* **repo:** tell the review bot which choices are deliberate ([4eb1cc1](https://github.com/Alberto-Codes/saucier/commit/4eb1cc1f2e3934da5b4023a9501f969628d60432))

## 0.0.1

Name reserved. No implementation.
