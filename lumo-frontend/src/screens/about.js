import React, { useState, useEffect } from "react";
import { Text, Link, ScrollView, Heading, Stack } from "native-base";
import Card from "../components/card";
import bandInfo from "../bands";

const AboutScreen = () => {
    const bands = ["7","8","10","14"];

    const renderBand = (prop) => {
        // console.log(`about: ${prop}`)
        // console.log(`about: ${bandInfo[prop]}`)
        return (
            <Stack key={bandInfo[prop].bandNum}>
                <Heading size="md">
                    About {bandInfo[prop].bandTitle}
                </Heading>
                <Text fontWeight="400">
                    {bandInfo[prop].bandDesc}
                </Text>
                <Text fontWeight="200">
                    Read more about {bandInfo[prop].bandTitle} <Link isExternal href={bandInfo[prop].bandUrl}>here.</Link>
                </Text>
            </Stack>
        );
    };

    return (
        <ScrollView>
            <Card>
                <Stack>
                    <Stack>
                        <Heading size="md">
                            What is Lumo?
                        </Heading>
                        <Text fontWeight="400">
                            Lumo is a project that aims to improve on current precipitation and weather prediction patterns using machine learning. This is done by collecting satellite imagery from several GOES bands and using Lumo's model to create a prediction of the band in the short term future.
                        </Text>
                    </Stack>
                    {bands.map((band) => {
                        return renderBand(band);
                    })}
                </Stack>
            </Card>
        </ScrollView>
    );
}

export default AboutScreen;