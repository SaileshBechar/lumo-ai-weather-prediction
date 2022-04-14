# Lumo
## Get started with _Conda_
1. Clone the repo
```
git clone git@github.com:SatchelCatral/lumo-app.git
```
2. Create and activate conda environment
```
cd lumo-app/DataRetrieval 
conda env create -f environment.yml
conda activate lumoenv
```
3. Run
```
python3 plot_script.py
```

## Docker
1. Clone the repo (see above)
2. Build the image
```
cd lumo-app/DataRetrieval
docker build .
```
After this successfully runs, you will see an image id at the end which is needed in the next step similar to
`Successfully built 1ed25ab9ecc3`. The image id can also be retrieved by running `docker images` and taking the most recent (topmost) image.

3. Run the container
```
docker run <IMAGE_ID>
```
## Useful Links
### FYDP Docs
 - [Followup Report](https://docs.google.com/document/d/1R7Cd-WXzcppu_Zht3ZMJtZUq7NWp_hnk7M23_x2j5kk/edit?usp=sharing)
 - [Detailed Design](https://docs.google.com/document/d/1fU9J6w1DTJvVt3n7nt1pje2YJ96QfSGZ6xZ5i8hhNao/edit)
 - [Spec and Risk](https://docs.google.com/document/d/1LgArWqL3U9CCffrYf27bBmj4YSO8LvlMl5RUU7fElR0/edit?usp=sharing)

### AI
 - [8 Hour Precipitation Forecasting - Google AI Blog](https://ai.googleblog.com/2020/03/a-neural-weather-model-for-eight-hour.html)
 - [Nowcasting - Google AI Blog](https://ai.googleblog.com/2020/01/using-machine-learning-to-nowcast.html?m=1)
### Data Retrieval
 - [Beginner's Guide to GOES-R](https://noaa-goes16.s3.amazonaws.com/Beginners_Guide_to_GOES-R_Series_Data.pdf)
 -  [Quick Guides for several satellite imagery](https://rammb.cira.colostate.edu/training/visit/quick_guides/)
 - [GOES Image Viewer](https://www.star.nesdis.noaa.gov/GOES/sector.php?sat=G16&sector=can)
