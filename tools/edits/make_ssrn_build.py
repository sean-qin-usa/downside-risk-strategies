# make_ssrn_build.py -- derive the SSRN reading copy from the journal-format source.
# Same text; single spacing, footnotes and floats inline, no endnote block. Writes
# paper/jfec/paper_A_ssrn.tex and paper/jfec/paper_A_ssrn_online_appendix.tex.
# Usage: python tools/edits/make_ssrn_build.py   (run from the repository root; then latexmk -pdf both)
import re
src="paper/jfec/paper_A_jfec.tex"; s=open(src,encoding="utf-8").read()
reps=[("\\usepackage{endnotes}\n",""),("\\usepackage[nolists]{endfloat}\n",""),("\\setstretch{2}","\\setstretch{1.15}"),
      ("\\let\\footnote\\endnote\n",""),
      ("\\begingroup\n\\parindent 0pt\\parskip 1ex\n\\renewcommand{\\enotesize}{\\normalsize}\n\\theendnotes\n\\endgroup\n","")]
for a,b in reps:
    assert s.count(a)==1,a; s=s.replace(a,b)
s=s.replace("\\bibliography{refs_v3}","\\bibliography{refs_v3}",1)
open("paper/jfec/paper_A_ssrn.tex","w",encoding="utf-8").write(s)
o=open("paper/jfec/paper_A_jfec_online_appendix.tex",encoding="utf-8").read()
open("paper/jfec/paper_A_ssrn_online_appendix.tex","w",encoding="utf-8").write(o)
print("wrote paper/jfec/paper_A_ssrn.tex and paper_A_ssrn_online_appendix.tex")
