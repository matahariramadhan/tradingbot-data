# Recovery-Capable Colab Notebook Update

Date: 2026-08-15

The maintained notebook now contains 26 cells, including 17 code cells. It
pins package commit
`6f5a0873b28024d62a72eb9f2411e79e9b299612` (`tradingbot-data` `0.4.0`) and adds:

1. a Drive-backed `proxy-recover` execution cell;
2. a separate recovered-target output directory;
3. a quality-verification cell that checks row shape, valid-target counts,
   recovered-row counts, and invalid quality flags;
4. a final stop before any model-ready join.

Local JSON parsing, compilation of all 17 code cells, and `git diff --check`
passed. The updated notebook has not yet been executed remotely, and the
package commit has not yet been pushed.
