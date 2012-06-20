from pylab import *

def make_data(base):
    clf()
    growth = transpose(genfromtxt(base + '.growth'))
    xlabel('Number of tokens')
    ylabel('Number of categories')
    plot(growth[0], growth[1])
    if size(growth, 0) > 2:
        plot(growth[0], growth[2])
    savefig(base + '.growth.png')
    
    clf()
    rank = transpose(genfromtxt(base + '.rank'))
    xlabel('Rank order (log)')
    ylabel('Frequency (log)')
    plot(rank, 'o')
    loglog()   
    savefig(base + '.rank.png')
    
if __name__ == '__main__':
    make_data('cats')
    make_data('rules')
