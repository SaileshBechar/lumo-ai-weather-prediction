export default {
    'C07': {
        bandNum: 7,
        bandTitle: '"Shortwave Window" Band - 3.9 µm',
        bandDesc: `2 km resolution - The 3.9 μm band can be used to identify fog and low clouds at night, identify fire hot spots, detect volcanic ash, estimate sea-surface temperatures, and discriminate between ice crystal sizes during the day. Low-level atmospheric vector winds can be estimated with this band.`,
        bandUrl: "https://www.star.nesdis.noaa.gov/GOES/documents/ABIQuickGuide_Band07.pdf",
        bandImg: require('./assets/band_7.png')
    }, 
    'C08': {
        bandNum: 8,
        bandTitle: 'Upper-level Water Vapor - 6.2 µm',
        bandDesc: `2 km resolution - Upper-level tropospheric water vapor tracking, jet stream identification, hurricane track forecasting, mid-latitude storm forecasting, severe weather analysis, upper mid-level moisture estimation and turbulence detection.\n`,
        bandUrl: "https://www.star.nesdis.noaa.gov/GOES/documents/ABIQuickGuide_Band08.pdf",
        bandImg: require('./assets/band_8.png')
    }, 
    'C09': { // DEPRECATED
        bandNum: 9,
        bandTitle: "9",
        bandDesc: `6.9 µm - "Mid-level Water Vapor" Band - 2 km resolution - Mid-level water vapor band. It is used for tracking middle-tropospheric winds, identifying jet streams, forecasting hurricane track and mid-latitude storm motion, monitoring severe weather potential, estimating mid-level moisture (for legacy vertical moisture profiles)and identifying regions where turbulence might exist. Surface features are usually not apparent in this band. Brightness Temperatures show cooling because of absorption of energy at 6.9 µm by water vapor.\nThe imager on GOES-16 features three mid-level water vapor bands instead of the single water vapor band on the GOES-13 Imager. The single water vapor band on GOES-13 contained a mixture of water vapor features over many levels of the troposphere, but GOES-16 enables us to focus on water vapor in the upper troposphere (band 8), the middle troposphere (band 9), or the lower troposphere (band 10). The GOES-13 Imager water vapor channel falls between ABI bands 8 and 9.`,
        bandUrl: "https://www.star.nesdis.noaa.gov/GOES/documents/ABIQuickGuide_Band09.pdf",
        bandImg: require('./assets/band_9.png')
    }, 
    'C10': {
        bandNum: 10,
        bandTitle: "Lower-level Water Vapor - 7.3 µm",
        bandDesc: `2 km resolution - This water vapor band typically senses farthest down into the midtroposphere in cloud-free regions, to around 500-750 hPa. It is used to track lowertropospheric winds and identify jet streaks.`,
        bandUrl: "https://www.star.nesdis.noaa.gov/GOES/documents/ABIQuickGuide_Band10.pdf",
        bandImg: require('./assets/band_10.png')
    }, 
    'C13': {
        bandNum: 13,
        bandTitle: '"Clean" Longwave IR Window Band - 10.3 µm',
        bandDesc: `2 km resolution - Band 13 at 10.3 µm is an infrared window, meaning it is not strongly affected by atmospheric water vapor. This channel is useful for detecting clouds all times of day and night and is particularly useful in retrievals of cloud top height.\nGOES-16 Band 13 corresponds approximately to the old GOES-13 IR cloud channel.`,
        bandUrl: "https://www.star.nesdis.noaa.gov/GOES/documents/ABIQuickGuide_Band13.pdf",
        bandImg: require('./assets/band_13.png')
    }, 
    'C14': {
        bandNum: 14,
        bandTitle: "Longwave IR Window Band - 11.6 µm",
        bandDesc: `2 km resolution - The traditional longwave infrared window band, is used to diagnose discrete clouds and organized features for general weather forecasting, analysis, and broadcasting applications. Observations from this IR window channel characterize atmospheric processes associated with extratropical cyclones and also in single thunderstorms and convective complexes.`,
        bandUrl: "https://www.star.nesdis.noaa.gov/GOES/documents/ABIQuickGuide_Band14.pdf",
        bandImg: require('./assets/band_14.png')
    }
}