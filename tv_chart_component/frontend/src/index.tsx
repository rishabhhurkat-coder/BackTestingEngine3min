import React from "react";
import ReactDOM from "react-dom/client";
import { withStreamlitConnection } from "streamlit-component-lib";
import Chart, { Candle, IndicatorSeries, Marker } from "./Chart";

type StreamlitArgs = {
  candles?: Candle[];
  indicators?: IndicatorSeries[];
  markers?: Marker[];
  chartType?: "Candlestick" | "Line Chart";
  showSessionBreaks?: boolean;
  height?: number;
};

const App = (props: any): React.ReactElement => {
  const args = (props?.args ?? {}) as StreamlitArgs;
  const candles = args.candles ?? [];
  const indicators = args.indicators ?? [];
  const markers = args.markers ?? [];
  const chartType = args.chartType ?? "Candlestick";
  const showSessionBreaks = args.showSessionBreaks ?? true;
  const height = args.height ?? 600;

  return (
    <Chart
      candles={candles}
      indicators={indicators}
      markers={markers}
      chartType={chartType}
      showSessionBreaks={showSessionBreaks}
      height={height}
    />
  );
};

const ConnectedApp = withStreamlitConnection(App);

const root = ReactDOM.createRoot(document.getElementById("root") as HTMLElement);
root.render(<ConnectedApp />);
