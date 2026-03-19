import React from "react";
import ReactDOM from "react-dom/client";
import { withStreamlitConnection } from "streamlit-component-lib";
import Chart, { Candle, EmaPoint, Marker } from "./Chart";

type StreamlitArgs = {
  candles?: Candle[];
  ema?: EmaPoint[];
  markers?: Marker[];
  height?: number;
};

const App = (props: any): JSX.Element => {
  const args = (props?.args ?? {}) as StreamlitArgs;
  const candles = args.candles ?? [];
  const ema = args.ema ?? [];
  const markers = args.markers ?? [];
  const height = args.height ?? 600;

  return (
    <Chart
      candles={candles}
      ema={ema}
      markers={markers}
      height={height}
    />
  );
};

const ConnectedApp = withStreamlitConnection(App);

const root = ReactDOM.createRoot(document.getElementById("root") as HTMLElement);
root.render(<ConnectedApp />);
