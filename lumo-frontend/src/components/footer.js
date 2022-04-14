import React from "react";
import { Box, Text, Icon, HStack, Center, Pressable } from "native-base";
import { MaterialCommunityIcons, MaterialIcons } from "@expo/vector-icons";

// DEPRECATED
const Footer = ({ onClick, tab }) => {

    return (
        <Box width="100%" alignSelf="center">
            <Center flex={1}></Center>
            <HStack bg="lightBlue.600" alignItems="center" safeAreaBottom shadow={6}>
                <Pressable opacity={tab === 'Home' ? 1 : 0.5} py="3" flex={1} onPress={() => onClick('Home')}>
                    <Center>
                    <Icon mb="1" as={<MaterialCommunityIcons name={tab === 'Home' ? "home" : "home-outline"} />} size="sm" />
                    <Text fontSize="12">
                        Home
                    </Text>
                    </Center>
                </Pressable>
                <Pressable opacity={tab === 'Home' ? 1 : 0.5} py="2" flex={1} onPress={() => onClick('About')}>
                    <Center>
                    <Icon mb="1" as={<MaterialIcons name="info" />} size="sm" />
                    <Text fontSize="12">
                        About
                    </Text>
                    </Center>
                </Pressable>
            </HStack>
        </Box>
    );
}

export default Footer