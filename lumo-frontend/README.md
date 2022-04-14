
# Lumo-frontend

## Getting Started

1. if the expo cli is not installed yet, run `npm install --global expo-cli`

2. create a `.env` file in the project folder with the following in it:
```
WEATHER_API_URL=http://api.openweathermap.org/data/2.5
WEATHER_API_KEY=<key>
```

3. run `npm install` or `yarn install`

4. run `expo start`

  

### Running on web browser

1. click **Run in web browser** from the expo client

  

### Running on Android/IOS

1. download the app **Expo Go** from the app store

2. inside the expo client, select the connection mode you want (I found that for my dev environment tunnel works)

3. If there is not a QR code or URL to scan, reload the expo client

4. Scan the QR code from the Expo Go application


### Deploying To Production

Lumo is hosted used AWS Amplify and uses the `production` branch on the repo

1. create a PR from `master` to `production`

2. once merged into `production`, AWS Amplify will detect changes and redeploy using the most recent commit