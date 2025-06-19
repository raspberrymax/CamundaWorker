# Slowed Down JSON Server <!-- omit from toc -->

A slowed down version of the [JSON Server](https://github.com/typicode/json-server) to simulate (randomly) slow requests.

The following diagrams show the results of a load test, proofing that the request time varies.

_HTTP Responses_
![Load Test: HTTP Responses](assets/http.responses.png)

<br>

_HTTP Response Time 2xx_
![Load Test: HTTP Response Time 2xx](assets/http.response_time.2xx.png)

# Table of Contents <!-- omit from toc -->

- [🚀Getting Started](#getting-started)
  - [CLI Options](#cli-options)
- [📈Load testing](#load-testing)

## 🚀Getting Started
w
Add your Data to the [server/db.json](server/db.json). The root keys will build your API Paths.

To start the server run the following commands:

```bash
# Install the dependencies
$ npm install

# Start the Server
$ npm start
```

You should see something like

> JSON Server is running on Port 3000

### CLI Options

You could use the following cli options (e.g. `npm run start -- --port=4000`)

- `--port` to set the Port of the Server. Default is `3000`
- `--data` to set the Path to your `db.json`, should be a relative path. Default is `./server/db.json`
- `--minRequestTime` to set the time a request should take at least. Default is `200`
- `--maxRequestTime` to set the time a request should take at most. Default is `2000`

## 📈Load testing

To do a load test start the server (`npm start`) and run `npm run load-test`. Have a look at the resulting [report](reports/test-run-report.json.html).
