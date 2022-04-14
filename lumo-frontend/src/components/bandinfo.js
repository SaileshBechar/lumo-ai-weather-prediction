import React, { useEffect, useState } from "react";
import { Box, Text, Heading, VStack, Link, HStack, Center, Image } from "native-base";
import Card from "./card";
import bandInfo from "../bands";

const BandInfo = ({ bandNum }) => {

    return (
        <Card>
            <VStack>
                <Heading size="md">
                    {bandInfo[bandNum]?.bandTitle}
                </Heading>
                <Text fontWeight="400" marginTop={"5"}>
                    {bandInfo[bandNum]?.bandDesc}
                </Text>
                <Text fontWeight="200">
                    <Link isExternal href={bandInfo[bandNum]?.bandUrl}>Source</Link>
                </Text>
            </VStack>
        </Card>
    );
}

export default BandInfo