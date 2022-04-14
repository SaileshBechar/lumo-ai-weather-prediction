import React, { useState, useEffect } from "react";
import { Stack, VStack, ScrollView, View } from "native-base";
import { Platform } from 'react-native';

// Constants
import {WEATHER_API_URL, WEATHER_API_KEY} from "@env"

// Components
import WeatherInfo from "./../components/weatherinfo"
import WeatherMap from "./../components/weathermap";
import ExampleWeatherMap from "./../components/weathermapexample";
import BandInfo from "./../components/bandinfo";

const WATERLOO_LATITUDE = 43.4844091;
const WATERLOO_LONGITUDE = -80.5327216;

const HomeScreen = () => {

    const [lat, setLat] = useState(WATERLOO_LATITUDE);
    const [long, setLong] = useState(WATERLOO_LONGITUDE);
    const [data, setData] = useState([]);
    const [bandNum, setBandNum] = useState(0);
  
    useEffect(() => {      
        const fetchData = async () => {
            await fetch(`${WEATHER_API_URL}/weather/?lat=${lat}&lon=${long}&units=metric&APPID=${WEATHER_API_KEY}`)
            .then(res => res.json())
            .then(result => {
                // console.log(result);
                setData(result);
            });
        }
        fetchData();
    }, []);

    const handleBandChange = (newBandNum) => {
        setBandNum(newBandNum);
    }

    return (
        <ScrollView bg={"#B7D9F5"}>
            <VStack>
                <Stack justifyContent="center" direction={Platform.OS == "android" || Platform.OS == "ios" ? "column" : "row"}>
                    <VStack maxWidth="500px">
                        <WeatherInfo weatherData={data} />
                        {(Platform.OS != "android" && Platform.OS != "ios" && bandNum != 0) && 
                            <BandInfo bandNum={bandNum} />
                        }
                    </VStack>
                    <WeatherMap onBandChange={handleBandChange} />
                </Stack>
                {Platform.OS != "android" && Platform.OS != "ios" && 
                    <ExampleWeatherMap />
                } 
            </VStack>
        </ScrollView>
    );
}

export default HomeScreen;