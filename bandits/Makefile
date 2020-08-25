.PHONY:all
all: internal-control-analysis.pdf

%.tex: %.md
	pandoc -s -f markdown -t latex -o $@ $<

%.pdf: %.tex
	latexmk -pdf

%.md: %.rmd internal-control-experiments.csv
	Rscript -e 'library(knitr); knit("$<",output="$@")' internal-control-experiments.csv

.PHONY:clean
clean:
	rm -rf *.md *.pdf *.fls *.log *.aux *latexmk __pycache__ cache figure

.PHONY:clean
browse: all
	qtb internal-control-analysis.html
