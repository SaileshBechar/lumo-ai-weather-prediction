import React, { useEffect, useState } from "react";
import { Box, Text, Heading, VStack, HStack, Center, Image } from "native-base";
import Card from "./card";

// DEPRECATED
const LumoPrediction = () => {

    const [isRaining, setIsRaining] = useState(false);
    const [period, setPeriod] = useState(10); // period of time it is currently raining/not raining
    const [granularity, setGranularity] = useState('minute');

    useEffect(() => {
        // TODO: Make a call to the backend to get prediction data

        // TODO: Set period: get max range from predicion (+30min / +2hr / etc) and subtract when it is predicted to rain/not rain
    }, [])

    return (
        <Card>
            <Heading 
                size="lg" 
                fontWeight="600" 
                color="coolGray.600" 
                _dark={{ color: "warmGray.50" }}
            >
                Lumo predicts that {isRaining ? "it is currently raining" : "it is currently NOT raining"}
            </Heading>
            <Text> and it will be like that for the next {period} {granularity}{period > 1 ? "s" : ""} </Text>
        </Card>
    );
}

export default LumoPrediction