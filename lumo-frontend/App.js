import React from 'react';
import { extendTheme, NativeBaseProvider, theme as nbTheme } from "native-base";
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Platform } from "react-native";

import HomeScreen from "./src/screens/home";
import AboutScreen from "./src/screens/about";

const theme = extendTheme({
  colors: {
    primary: {
        50:  "#5DA9E9",
        100: "#5DA9E9",
        200: "#5DA9E9",
        300: "#5DA9E9",
        400: "#5DA9E9",
        500: "#5DA9E9",
        600: "#5DA9E9",
        700: "#5DA9E9",
        800: "#5DA9E9",
        900: "#5DA9E9",
    },
    // primary: nbTheme.colors.blueGray,
  },
});

// const Stack = createNativeStackNavigator();
const Tab = createBottomTabNavigator();

export default function App() {

  return (
    // TODO: NativeBaseProvider allows us to pass in theming (Light + Dark mode)
    <NativeBaseProvider theme={theme}>
      <NavigationContainer>
        <Tab.Navigator navigationOptions={{header: null}}>
          <Tab.Screen name="Home" component={HomeScreen}  options={{
            headerShown: false,
          }} />
          {Platform.OS == "android" || Platform.OS == "ios" && 
            <Tab.Screen name="About" component={AboutScreen} />
          }
        </Tab.Navigator>
      </NavigationContainer>
    </NativeBaseProvider>
  );
}
