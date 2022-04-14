import React from "react";
import { Box, Center } from "native-base";

const Card = (props) => {
    return (
        <Box safeArea p="20" m="2" py="8" rounded="lg" borderColor="#766C7F" borderWidth="0" alignItems="center" justifyContent={"center"}
            bg={"#FEFCFB"} >
            {props.children}
        </Box>
    );
}

export default Card