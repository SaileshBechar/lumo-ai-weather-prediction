import React, { useEffect, useState } from "react";
import useInterval from "use-interval";
import { Button, Text, Heading, VStack, HStack, Center, Image, Icon, Skeleton, Link } from "native-base";
import Card from "./card";
import { Platform, Dimensions } from 'react-native';
import { Entypo  } from "@expo/vector-icons";
import axios from 'axios';
import bandInfo from '../bands';

const deviceWidth = Dimensions.get('window').width;

const imgWidth = 439;
const imgHeight = 558;
const imgRatio = imgWidth / imgHeight;

const colorBandWidth = 437;
const colorBandHeight = 58;
const colorBandRatio = colorBandWidth / colorBandHeight;

const BAND_DICT = {
    "C07" : '"Shortwave Window" Band - 3.9 µm',
    "C08" : "Upper-level Water Vapor - 6.2 µm",
    "C10" : "Lower-level Water Vapor - 7.3 µm",
    "C13" : '"Clean" Longwave IR Window Band - 10.3 µm',
    "C14" : "Longwave IR Window Band - 11.6 µm"
}

const WeatherMap = ({ onBandChange }) => {

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
        // let path = isGroundTruth ? "gt" : "predictions";
        for (const band of bands) {
            axios.get(`https://sanujsyal.com/predictions?band=${band}`, { crossdomain: true })
            .then(predictions => {
                axios.get(`https://sanujsyal.com/gt?band=${band}`, { crossdomain: true })
                .then(truths => {
                    if (predictions.data.length > 0 && truths.data.length > 0) {
                        setData(prevState => (
                            [...prevState, {
                                band: band,
                                data: 
                                    truths.data.map(data => ({
                                        timestamp: formatDate(data['timestamp']),
                                        url: data['url']
                                    })).concat(
                                    predictions.data.map(data => ({
                                        timestamp: formatDate(data['timestamp']),
                                        url: data['url']
                                    })))
                            }]
                        ));
                    }
                })
                .catch(err2 => console.log(err2));
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
        onBandChange(data[bandIndex]?.band);
    }, [data]);

    useInterval(() => {
        setImgIndex(prevIndex => {
            if (prevIndex >= data[bandIndex]?.data.length - 1) return 0;
            else return prevIndex + 1;
        });
    }, !paused ? period : null);

    const handleUpdateBandIndex = (nextBand = true) => {
        if (nextBand) {
            setBandIndex(prevIndex => {
                if (prevIndex >= data.length - 1) {
                    onBandChange(data[0]?.band);
                    return 0
                }
                else {
                    onBandChange(data[prevIndex + 1]?.band);
                    return prevIndex + 1;
                }
            });
        } else {
            setBandIndex(prevIndex => {
                if (prevIndex <= 0) {
                    onBandChange(data[data.length - 1]?.band);
                    return data.length - 1;
                }
                else {
                    onBandChange(data[prevIndex - 1]?.band);
                    return prevIndex - 1;
                }
            });
        }
        setImgIndex(0);
    }

    const handleUpdateImgIndex = (nextImg = true) => {
        if (nextImg) {
            setImgIndex(prevIndex => {
                if (prevIndex >= data[bandIndex]?.data?.length - 1) return 0
                else return prevIndex + 1;
            });
        } else {
            setImgIndex(prevIndex => {
                if (prevIndex <= 0) return data[bandIndex]?.data?.length - 1;
                else return prevIndex - 1;
            });
        }
    }

    const handleUpdatePlayback = () => {
        setPaused(prevState => !prevState);
    }

    return (
        <Card>
            <VStack alignItems={"center"}>
                { Platform.OS == "android" || Platform.OS == "ios" ?
                    <Image
                        source={{ uri: data[bandIndex]?.data[imgIndex]?.url, }} 
                        width={(deviceWidth * 0.8) > imgWidth ? imgWidth : (deviceWidth * 0.8)}
                        height={(deviceWidth * 0.8 * imgRatio) > imgHeight ? imgHeight : (deviceWidth * 0.8 * imgRatio)}
                        alt="Alt"
                    /> : 
                    data[bandIndex]?.data?.map((map, i) => 
                        <Image 
                            key={map.timestamp + i}
                            source={{ uri: map.url, }} 
                            width={(deviceWidth * 0.8) > imgWidth ? imgWidth : (deviceWidth * 0.8)}
                            height={(deviceWidth * 0.8 * imgRatio) > imgHeight ? imgHeight : (deviceWidth * 0.8 * imgRatio)}
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
                {data[bandIndex]?.band && 
                    <Image
                        key={data[bandIndex]?.band}
                        source={bandInfo[data[bandIndex]?.band].bandImg}
                        alt="Alt"
                        width={(deviceWidth * 0.8) > colorBandWidth ? colorBandWidth : (deviceWidth * 0.8)}
                        height={(deviceWidth * 0.8 * colorBandRatio) > colorBandHeight ? colorBandHeight : (deviceWidth * 0.8 * colorBandRatio)}
                    />
                }
                <HStack p="2">
                    <Button leftIcon={<Icon as={Entypo} name="controller-fast-backward" size="sm"/>} m="0.5" onPress={() => handleUpdateBandIndex(false)} />
                    <Button leftIcon={<Icon as={Entypo} name="controller-jump-to-start" size="sm"/>} m="0.5" onPress={() => handleUpdateImgIndex(false)} />
                    <Button leftIcon={<Icon as={Entypo} name={paused ? "controller-play" : "controller-paus"} size="sm"/>} m="0.5" onPress={() => handleUpdatePlayback()} />
                    <Button leftIcon={<Icon as={Entypo} name="controller-next" size="sm"/>} m="0.5" onPress={() => handleUpdateImgIndex()} />
                    <Button leftIcon={<Icon as={Entypo} name="controller-fast-forward" size="sm"/>} m="0.5" onPress={() => handleUpdateBandIndex()} />
                </HStack>                
                <VStack>
                    <Heading size="md">{BAND_DICT[data[bandIndex]?.band]}</Heading>
                    <Text fontWeight="400" textAlign={"center"}>{data[bandIndex]?.data[imgIndex]?.timestamp}</Text>
                    {/* <Text fontWeight="200">bandIdx: {bandIndex} imgIdx: {imgIndex}</Text> */}
                </VStack>
            </VStack>
        </Card>
    );
}

export default WeatherMap