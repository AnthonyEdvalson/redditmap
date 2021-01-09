# redditmap

This is my final project for my Data Visualization class. The goal was to collect, analyze, and present data about a social media site.

For my project, I created an interactive map of Reddit that shows subreddits and their relationships. 
The final product can be viewed online [here](https://anthonyedvalson.github.io/redditmap/)
(Note: the data contains adult topics, don't view unless you are 18+). Scroll to zoom, click to highlight, and drag to pan.

## Terms
If you aren't familiar with Reddit, here are the terms you need to know to understand the rest of this readme:

**Subreddits:** Also called "subs", are communities that are built around a particular topic. They range from memes, to personal finance, to stamp collecting.
Users can then post on a subreddit about that topic.

**Subscribers:** Users who are interested in a particular subreddit can subscribe to them to see new posts on that subreddit.


## Data Collection
The goal of the data collection phase is to get all information needed to calculate the relatedness of all pairs subreddits. 
The way I did this, is a recursive search over all of Reddit, the rough outline is the following:

1. Get information about a subreddit
2. Find users that have recently interacted with that subreddit
3. Get information about those users
4. Find subreddits that those users have recently interacted with
5. Repeat with the newly found subreddits

To prevent it from repeating forever, I only sampled one user in every 22,500 on the site, and ignored subreddits that had less than 4 users sampled in them to reduce noise.

The strategy I just described works well enough, but there's a clever optimization trick that makes it 8 times faster. 

### Beta Distribution 
The problem with the above algorithm is filtering subreddits. The naive way to filter is to check the size, if it's too small, it's ignored. 
The problem is that checking the size of a subreddit requires an API call. If it was possible to know how popular a subreddit is without checking, 
the algorithm would be 8 times as fast.

The way this can be done, is by leveraging the data already collected. Intuitively, more popular subreddits will appear more often in the data. This intuition can
be formalized with the beta distribution ([this](http://varianceexplained.org/statistics/beta_distribution_and_baseball/) blog post gives a great explanation of how to use it).

I then adapted the search so that it would not look into a subreddit unless it was 90% certain that it was large enough to be in the results.
This improved performance, allowing the full search to finish in a day instead of a week.

## Data Processing

The collected data is stored as relationships between users and subreddits, but the visualization needs relationships between subreddits and other subreddits.
This was done by the Jaccard index, which I modified to compare the ratio of shared interactions between all pairs of subreddits.
Afterwards, all edges with a strength less than 0.1 are discarded, otherwise there are far too many edges in the rendering stage.


## Data Visualization

The UI is a force directed graph. There are a number of forces applied to each node. A spring force is applied along the edges, strong edges pull tigher than weak one. There is also strong repulsive force between all vertices, together these forces make clusters more distinct. 


## Conclusion

A lot of time and thought went into this project, it's easily my favorite school project I've done at RIT. The full report is available [here](https://docs.google.com/document/d/1_vshGcIGUmvLzSv5qEqXOi9oBIF0W9SPeSOrlGm9rZA/edit?usp=sharing),
and the presentation [here](https://docs.google.com/presentation/d/1vqsLJG2nY51LtXgptzHhcsq1yN1ptCFzBbhKfk0R9H0/edit?usp=sharing). If you have questions or feedback
feel free to email me at anthonyedvalson@gmail.com
