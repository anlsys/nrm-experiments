.PHONY:all
all: internal-control-analysis.pdf

%.tex: %.md
	pandoc -s -f markdown -t latex -o $@ $<

%.pdf: %.tex
	latexmk -pdf

%.md: %.rmd
	Rscript -e 'library(knitr); knit("$<",output="$@")' internal-control-experiments.csv

.PHONY:clean
clean:
	rm -f *.md *.pdf

.PHONY:clean
browse: all
	qtb internal-control-analysis.html
