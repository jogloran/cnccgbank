from matplotlib import rc
rc('font',**{'family':'serif','serif':['Times']})
rc('text', usetex=True)
   
from pylab import *

def make_data(base, yname):
    clf()
    growth = transpose(genfromtxt(base + '.growth'))
    xlabel(r'\textit{Number of tokens}')
    ylabel(r'\textit{Number of ' + yname + '}')
    plot(growth[0], growth[1])
    if size(growth, 0) > 2:
        plot(growth[0], growth[2], '--')
        legend([ 'All', '$f \ge 5$' ], 'best')
    savefig(base + '.growth.pdf')
    
    clf()
    rank = transpose(genfromtxt(base + '.rank'))
    xlabel(r'\textit{Rank order} ($\log$)')
    ylabel(r'\textit{Frequency} ($\log$)')

    plot(rank, 'o')
    loglog()   
    savefig(base + '.rank.pdf')
    
if __name__ == '__main__':
    make_data('cats', yname='categories')
    make_data('rules', yname='rule types')
