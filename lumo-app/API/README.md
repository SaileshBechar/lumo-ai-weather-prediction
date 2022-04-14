# Backend API

Domain is at https://sanujsyal.com

### `/fetch`
Fetches any item or items.

https://sanujsyal.com/fetch?path=examples/predictions/C07.
- `path` = File path of item(s) to fetch. Defaults to `examples/ground-truths/C07/`.

```
{
    "filename": File name,
    "url": Public S3 url to file,
    "last_modified": Date of last modification,
    "timestamp": Timestamp of parsed from file name
}
```

### `/example-predictions`
Returns every other predicted items within the GOES example directory

https://sanujsyal.com/example-predictions
- `band` = (**C07** | C08 | C09 | C10 | C13 | C14) Specifies the band

```
{
    "filename": File name,
    "url": Public S3 url to file,
    "last_modified": Date of last modification,
    "timestamp": Timestamp of parsed from file name
}
```


## GOES

### `/predictions`

https://sanujsyal.com/predictions?band=C08.
- `band` = (**C07** | C08 | C09 | C10 | C13 | C14) Specifies the band

Returns a list of the following:
```
{
    "filename": File name,
    "url": Public S3 url to file,
    "last_modified": Date of last modification,
    "timestamp": Timestamp of prediction,
    "cloud_str": (sun|cloud|partly) String dictating cloud cover conditions
}
```



### `/gt` (Ground Truths)

E.g. https://sanujsyal.com/gt?band=C08.
- `band` = (**C07** | C08 | C09 | C10 | C13 | C14) Specifies the band

Returns a 9-element list of the following:
```
{
    "filename": File name,
    "url": Public S3 url to file,
    "last_modified": Date of last modification,
    "timestamp": Timestamp of ground truth
}
```

## MRMS

### `/mrms-predictions`

E.g. https://sanujsyal.com/mrms-predictions?type=24.
- `type` = (**24** | 1) Specifies 24 hour or 1 hour predictions

Returns a list of the following:
```
{
    "filename": File name,
    "url": Public S3 url to file,
    "last_modified": Date of last modification,
    "timestamp": Timestamp of prediction,
    "rainfall": {
      "img_index": Image index,
      "percentage": Percentage chance of rain
      "rain_intensity": Some sort of rain intensity scale???
    }
}
```



### `/mrms-gt`

E.g. https://sanujsyal.com/mrms-gt.

Returns a 9-element list of the following:
```
{
    "filename": File name,
    "url": Public S3 url to file,
    "last_modified": Date of last modification,
    "timestamp": Timestamp of ground truth
}
```