# redditmap

This is my final project for my Data Visualization class. The goal was to collect, analyze, and present data about a social media site.

For my project I created an interactive map of Reddit that shows subreddits and their relationships. 
The final product can be viewed online [here](https://anthonyedvalson.github.io/redditmap/)
(Note: the data contains adult topics, don't view unless you are 18+). Scroll to zoom, click on vertices to highlight their neighbors, and drag to pan.

## Terms
If you aren't familiar with Reddit, here are the terms you need to know to understand the rest of this readme:

**Subreddits:** Also called "subs", are communities that are built around a particular topic. They range from memes, to personal finance, to stamp collecting.
Users can then post on a subreddit about that topic.

**Subscribers:** Users who are interested in a particular subreddit can subscribe to them to see new posts on that subreddit


## Data Collection
The goal of the data collection phase is to get all information needed to calculate the relatedness of two subreddits. 
The way I did this is a recursive search over all of Reddit, the rough outline is the following:

1. Get information about a subreddit
2. Find users that have recently interacted with that subreddit
3. Get information about those users
4. Find subreddits that those users have recently interacted with
5. Repeat with the newly found subreddits

To prevent it from repeating forever, I only sampled one user in every 22,500 on the site, and ignored subreddits that had less than 4 users sampled in them to reduce noise.

The strategy I just described works well enough, but there's a clever optimization trick that makes it 8 times faster. 

### Beta Distribution 
The problem with the above algorithm is filtering subreddits. The naive way to filter is to check the size of a subreddit, if it's too small, it's ignored. 
The problem is that checking the size of a subreddit takes an API call. If it was possible to know how popular a subreddit is without checking, 
the algorithm would be 8 times as fast.

The way this can be done, is by leveraging the data already collected. Intuitively, more popular subreddits will appear more in the data. This intuition can
be formalized with the beta distribution ([this](http://varianceexplained.org/statistics/beta_distribution_and_baseball/) blog post gives a great explanation of how to use it).

I then adapted the search so that it would not look into a subreddit unless it was 90% certain that it was large enough to be in the results.
This improved performance, allowing the full search to finish in a day instead of a week.


## Data Processing

The collected data is stored as relationships between users and subreddits, but the visualization needs relationships between subreddits and other subreddits.
This was done by the jaccard index, which I modified to compare the ratio of shared interactions between all pairs of subreddits.
Afterwards, all edges with a strength less than 0.1 are discarded, otherwise there are far too many edges in the rendering stage.


## Data Visualization

I wanted the UI to look nice and be very intuitive. I based the visualizations on [this](https://i.redd.it/va0hrlzdqet41.png) image. The data is fairly clear and doesn’t need too much explanation 
for someone to understand, which is something I strive for in all of my visualizations. I wanted it to be interactive and online, that way it’s easier to 
navigate and understand the relationships. 

The UI centers around a force directed graph. On startup it shows an animation of all of the forces pushing and pulling on the vertices, trying to find some 
structure. There are a number of forces applied to each node. First is a weak attractive force towards the origin, this keeps the nodes from drifting too far 
away. Second, a spring force is applied along the edges. These springs have a desired length based on how strong of an edge it is, stronger edges will pull in 
tightly, and weak ones will prefer a further distance. Lastly there is a strong repulsive force between all vertices, this is to make sure vertices avoid each 
other unless they are being pulled together, making the clusters more distinct. The edges also change color depending on how strong of a connection they have, 
strong ties will be bright white, and weak ones will be fainter.

The graph also has a simple selecting system, when hovering or clicking on a subreddit, the related links will highlight orange, which is very useful in the 
middle of the graph where the edges are easy to lose. Lastly I added a simple search functionality so if the user has a particular subreddit in mind they can 
look it up to zoom in on it.


## Conclusion

A lot of time and thought went into this project, it's easily my favorite school project I've done at RIT. The full report is available [here](https://docs.google.com/document/d/1_vshGcIGUmvLzSv5qEqXOi9oBIF0W9SPeSOrlGm9rZA/edit?usp=sharing),
and the presentation [here](https://docs.google.com/presentation/d/1vqsLJG2nY51LtXgptzHhcsq1yN1ptCFzBbhKfk0R9H0/edit?usp=sharing). If you have questions or feedback
feel free to email me at anthonyedvalson@gmail.com
