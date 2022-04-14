import React, { useEffect } from "react";
import { Box, Text, Heading, VStack, HStack, Center, Divider, Icon, Image } from "native-base";
import Card from "./card";
import { Platform, Dimensions } from "react-native";

const deviceWidth = Dimensions.get('window').width;
const imgWidth = 200;
const imgHeight = 200;
const imgRatio = imgWidth / imgHeight;

const WeatherInfo = ({weatherData}) => {

    useEffect(() => {
            // console.log(weatherData);
    }, [weatherData]);

    const renderInfo = () => {
        if (Platform.OS == "android" || Platform.OS == "ios") {
            return (
                <VStack space={6}>
                    <Text fontWeight="medium"><Text color="coolGray.600">Sunrise:</Text> {weatherData.sys && new Date(weatherData.sys.sunrise * 1000).toLocaleTimeString('en-IN')} </Text>
                    <Text fontWeight="medium"><Text color="coolGray.600">Sunset:</Text> {weatherData.sys && new Date(weatherData.sys.sunset * 1000).toLocaleTimeString('en-IN')} </Text>
                    {/* <Divider my="2" /> */}
                    <Text fontWeight="medium"><Text color="coolGray.600">Temperature:</Text> {weatherData.main && weatherData.main.temp} &deg;C </Text>
                    <Text fontWeight="medium"><Text color="coolGray.600">Feels Like:</Text> {weatherData.main && weatherData.main.feels_like} &deg;C </Text>
                    <Text fontWeight="medium"><Text color="coolGray.600">Humidity:</Text> {weatherData.main && weatherData.main.humidity} % </Text>
                    {/* <Divider my="2" /> */}
                    <Text fontWeight="medium"><Text color="coolGray.600">Weather:</Text> {weatherData.weather && weatherData.weather[0].main} </Text>
                </VStack>
            );
        } else {
            return (
                <HStack p="2" space={3} mt="5" justifyContent="center">
                    <VStack space={2}>
                        <Text fontWeight="medium"><Text color="coolGray.600">Sunrise:</Text> {weatherData.sys && new Date(weatherData.sys.sunrise * 1000).toLocaleTimeString('en-IN')} </Text>
                        <Text fontWeight="medium"><Text color="coolGray.600">Sunset:</Text> {weatherData.sys && new Date(weatherData.sys.sunset * 1000).toLocaleTimeString('en-IN')} </Text>
                    </VStack>       
                    <VStack space={3}>
                        <Text fontWeight="medium"><Text color="coolGray.600">Temperature:</Text> {weatherData.main && weatherData.main.temp} &deg;C </Text>
                        <Text fontWeight="medium"><Text color="coolGray.600">Feels Like:</Text> {weatherData.main && weatherData.main.feels_like} &deg;C </Text>
                        <Text fontWeight="medium"><Text color="coolGray.600">Humidity:</Text> {weatherData.main && weatherData.main.humidity} % </Text>
                    </VStack>
                    <VStack space={2}>
                        <Text fontWeight="medium"><Text color="coolGray.600">Weather:</Text> {weatherData.weather && weatherData.weather[0].main} </Text>

                    </VStack>
                </HStack>
            );
        }
    }

    return ( weatherData &&
        <Card>
            <Heading 
                size="lg" 
                fontWeight="600" 
                color="coolGray.800" 
                _dark={{ color: "warmGray.50" }}
            >
                <Image 
                    source={{ uri: require('./../assets/icon.png') }}
                    alt="Lumo_Icon"
                    width={(deviceWidth * 0.8) > imgWidth ? imgWidth : (deviceWidth * 0.8)}
                    height={(deviceWidth * 0.8 * imgRatio) > imgHeight ? imgHeight : (deviceWidth * 0.8 * imgRatio)}
                />
            </Heading>
            <Heading 
                mt="1" 
                _dark={{ color: "warmGray.200" }} 
                color="coolGray.600" 
                fontWeight="medium" 
                size="xs"
            >
                Location: {weatherData.name}, {weatherData.sys && weatherData.sys.country}
            </Heading>

            {renderInfo()}
        </Card>
    );
}

export default WeatherInfo