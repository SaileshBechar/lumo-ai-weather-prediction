import React, { useEffect, useState } from "react";
import useInterval from "use-interval";
import { Button, Text, Heading, VStack, HStack, Stack, Center, Image, Icon, Skeleton } from "native-base";
import Card from "./card";
import { Platform, Dimensions } from 'react-native';
import { Entypo  } from "@expo/vector-icons";
import axios from 'axios';
import bandInfo from '../bands';

const deviceWidth = Platform.OS == "android" || Platform.OS == "ios" ? Dimensions.get('window').width : (Dimensions.get('window').width / 3);

const imgWidth = 439;
const imgHeight = 558;
const imgRatio = imgWidth / imgHeight;

const colorBandWidth = 437;
const colorBandHeight = 58;
const colorBandRatio = colorBandWidth / colorBandHeight;

const rmseWidth = 579;
const rmseHeight = 587;
const rmseRatio = imgWidth / imgHeight; // 0.98637

const BAND_DICT = {
    "C07" : '"Shortwave Window" Band - 3.9 µm',
    "C08" : "Upper-level Water Vapor - 6.2 µm",
    "C10" : "Lower-level Water Vapor - 7.3 µm",
    "C13" : '"Clean" Longwave IR Window Band - 10.3 µm',
    "C14" : "Longwave IR Window Band - 11.6 µm"
}

const ExampleWeatherMap = () => {

    const bands = ["C07","C08","C10","C14"];
    const [bandIndex, setBandIndex] = useState(0);
    const [imgIndex, setImgIndex] = useState(0);
    const [paused, setPaused] = useState(false);
    const [fetched, setFetched] = useState(false);
    const [data, setData] = useState([]);
    const period = 668; //167;

    const formatDate = (date) => {
        let dateObj = new Date(date);
        let ampm = dateObj.getHours() >= 12 ? 'PM' : 'AM'
        let hours = dateObj.getHours() % 12 ? dateObj.getHours() % 12 : '0'
        let minutes = (dateObj.getMinutes() < 10 ? '0' : '') + dateObj.getMinutes();
        return `${dateObj.getDate()}/${dateObj.getMonth() + 1}/${dateObj.getFullYear()} ${hours}:${minutes} ${ampm} (EST)`;
    }

    const fetchPredictions = () => {
        for (const band of bands) {
            axios.get(`https://sanujsyal.com/example-predictions?band=${band}`, { crossdomain: true })
            .then(predictions => {
                axios.get(`https://sanujsyal.com/fetch?path=examples/ground-truths/${band}`, { crossdomain: true })
                .then(truths => {
                    axios.get(`https://sanujsyal.com/fetch?path=examples/rmse/${band}`, { crossdomain: true })
                    .then(rmses => {
                        if (truths.data.length > 0 && predictions.data.length > 0 && rmses.data.length > 0) {
                            setData(prevState => (
                                [...prevState, {
                                    band: band,
                                    predictions: predictions.data.map(data => ({
                                        timestamp: formatDate(data['timestamp']),
                                        url: data['url']
                                    })),
                                    truths: truths.data.map(data => ({
                                        timestamp: formatDate(data['timestamp']),
                                        url: data['url']
                                    })),
                                    rmse: rmses.data.map(data => ({
                                        url: data['url']
                                    }))
                                }]
                            ))
                        } 
                    })
                    .catch(err3 => console.log(err3))
                })
                .catch(err2 => console.log(err2))
            })
            .catch(err => console.log(err));
        }
    }

    useEffect(() => {
        if (!fetched) {
            fetchPredictions();
            setFetched(true);
        }
    });

    useEffect(() => {
        console.log(data);
    }, [data]);

    useInterval(() => {
        setImgIndex(prevIndex => {
            if (prevIndex >= data[bandIndex]?.truths.length - 1) return 0;
            else return prevIndex + 1;
        });
    }, !paused ? period : null);

    const handleUpdateBandIndex = (nextBand = true) => {
        if (nextBand) {
            setBandIndex(prevIndex => {
                if (prevIndex >= data.length - 1) return 0
                else return prevIndex + 1;
            });
        } else {
            setBandIndex(prevIndex => {
                if (prevIndex <= 0) return data.length - 1;
                else return prevIndex - 1;
            });
        }
        setImgIndex(0);
    }

    const handleUpdateImgIndex = (nextImg = true) => {
        if (nextImg) {
            setImgIndex(prevIndex => {
                if (prevIndex >= data[bandIndex]?.truths?.length - 1) return 0
                else return prevIndex + 1;
            });
        } else {
            setImgIndex(prevIndex => {
                if (prevIndex <= 0) return data[bandIndex]?.truths?.length - 1;
                else return prevIndex - 1;
            });
        }
    }

    const handleUpdatePlayback = () => {
        setPaused(prevState => !prevState);
    }

    return (
        <Card justifyContent={"center"}>
            <VStack alignItems={"center"}>
                <HStack justifyContent={"space-evenly"} width="fill-available">
                    <Text fontWeight="600">Ground Truths</Text>
                    <Text fontWeight="600">Lumo Predictions</Text>
                    <Text fontWeight="600">RMSE</Text>
                </HStack>
                <Stack direction={Platform.OS == "android" || Platform.OS == "ios" ? "column" : "row"} 
                    justifyContent={"space-evenly"}>
                    { Platform.OS == "android" || Platform.OS == "ios" ?
                        <Image
                            source={{ uri: data[bandIndex]?.truths[imgIndex]?.url, }} 
                            width={(deviceWidth * 0.8) > imgWidth ? imgWidth : (deviceWidth * 0.8)}
                            height={(deviceWidth * 0.8 * imgRatio) > imgHeight ? imgHeight : (deviceWidth * 0.8 * imgRatio)}
                            alt="Alt"
                        /> : 
                        data[bandIndex]?.truths?.map((map, i) => 
                            <Image 
                                key={map.timestamp + i}
                                source={{ uri: map.url, }} 
                                width={(deviceWidth * 0.8) > imgWidth ? imgWidth : (deviceWidth * 0.8)}
                                // height={imgHeight}
                                height={(deviceWidth * 0.8 * imgRatio) > imgHeight ? imgHeight : (deviceWidth * 0.8 * imgRatio)}
                                resizeMode={"contain"}
                                alt="Alt"
                                style={{ 
                                    visibility: imgIndex == i ? "visible" : "hidden",
                                    zIndex: 90 + i,
                                    opacity: imgIndex == i ? "1" : "0",
                                    display: imgIndex == i ? "block" : "none",
                                    // top: 0,
                                    // left: 0,
                                    // position: "absolute"
                                }}
                            />
                        )
                    }
                    { Platform.OS == "android" || Platform.OS == "ios" ?
                        <Image
                            source={{ uri: data[bandIndex]?.predictions[imgIndex]?.url, }} 
                            width={(deviceWidth * 0.8) > imgWidth ? imgWidth : (deviceWidth * 0.8)}
                            height={(deviceWidth * 0.8 * imgRatio) > imgHeight ? imgHeight : (deviceWidth * 0.8 * imgRatio)}
                            alt="Alt"
                        /> : 
                        data[bandIndex]?.predictions?.map((map, i) => 
                            <Image 
                                key={map.timestamp + i}
                                source={{ uri: map.url, }} 
                                width={(deviceWidth * 0.8) > imgWidth ? imgWidth : (deviceWidth * 0.8)}
                                // height={imgHeight}
                                height={(deviceWidth * 0.8 * imgRatio) > imgHeight ? imgHeight : (deviceWidth * 0.8 * imgRatio)}
                                resizeMode={"contain"}
                                alt="Alt"
                                style={{ 
                                    visibility: imgIndex == i ? "visible" : "hidden",
                                    zIndex: 90 + i,
                                    opacity: imgIndex == i ? "1" : "0",
                                    display: imgIndex == i ? "block" : "none",
                                    // top: 0,
                                    // left: 0,
                                    // position: "absolute"
                                }}
                            />
                        )
                    }
                    <Image
                        source={{ uri: data[bandIndex]?.rmse[0]?.url }}
                        width={(deviceWidth * 0.8) > rmseWidth ? rmseWidth : (deviceWidth * 0.8)}
                        // height={rmseHeight}
                        height={(deviceWidth * 0.8 * rmseRatio) > rmseHeight ? rmseHeight : (deviceWidth * 1.05 * rmseRatio)}
                        alt="rmse_alt"
                    />
                </Stack>                
                {data[bandIndex]?.band && 
                    <Image
                        key={data[bandIndex]?.band}
                        source={bandInfo[data[bandIndex]?.band].bandImg}
                        alt="Alt"
                        width={(deviceWidth * 0.8) > colorBandWidth ? colorBandWidth : (deviceWidth * 0.8)}
                        height={(deviceWidth * 0.8 * colorBandRatio) > colorBandHeight ? colorBandHeight : (deviceWidth * 0.8 * colorBandRatio)}
                        resizeMode={"contain"}
                    />
                }
                <HStack p="2">
                    <Button leftIcon={<Icon as={Entypo} name="controller-fast-backward" size="sm"/>} m="0.5" onPress={() => handleUpdateBandIndex(false)} />
                    <Button leftIcon={<Icon as={Entypo} name="controller-jump-to-start" size="sm"/>} m="0.5" onPress={() => handleUpdateImgIndex(false)} />
                    <Button leftIcon={<Icon as={Entypo} name={paused ? "controller-play" : "controller-paus"} size="sm"/>} m="0.5" onPress={() => handleUpdatePlayback()} />
                    <Button leftIcon={<Icon as={Entypo} name="controller-next" size="sm"/>} m="0.5" onPress={() => handleUpdateImgIndex()} />
                    <Button leftIcon={<Icon as={Entypo} name="controller-fast-forward" size="sm" />} m="0.5" onPress={() => handleUpdateBandIndex()} />
                </HStack>                
                <VStack>
                    <Heading size="md">{BAND_DICT[data[bandIndex]?.band]}</Heading>
                    <Text fontWeight="400" textAlign={"center"}>{data[bandIndex]?.truths[imgIndex]?.timestamp}</Text>
                    {/* <Text fontWeight="400">Predictions Timestamp: {data[bandIndex]?.predictions[imgIndex]?.timestamp}</Text> */}
                    {/* <Text fontWeight="200">bandIdx: {bandIndex} imgIdx: {imgIndex}</Text> */}
                </VStack>
            </VStack>
        </Card>
    );
}

export default ExampleWeatherMap