import React, { useEffect, useRef } from "react";
import {
  CandlestickData,
  LineData,
  UTCTimestamp,
  createChart,
  IChartApi,
  ISeriesApi,
  SeriesMarker,
} from "lightweight-charts";
import { Streamlit } from "streamlit-component-lib";

export type Candle = {
  time: string | number;
  open: number;
  high: number;
  low: number;
  close: number;
};

export type EmaPoint = {
  time: string | number;
  value: number;
};

export type Marker = {
  time: string | number;
  position: "aboveBar" | "belowBar" | "inBar";
  shape: "arrowUp" | "arrowDown" | "circle" | "square";
  color: string;
  text?: string;
};

type ChartProps = {
  candles: Candle[];
  ema: EmaPoint[];
  markers?: Marker[];
  height?: number;
};

const toTimestamp = (value: string | number): UTCTimestamp | null => {
  if (typeof value === "number" && Number.isFinite(value)) {
    return Math.trunc(value) as UTCTimestamp;
  }

  const text = String(value).trim();
  if (!text) {
    return null;
  }

  if (/^\d+$/.test(text)) {
    return Number(text) as UTCTimestamp;
  }

  const normalized = text.includes("T") ? text : text.replace(" ", "T");
  const parsed = Date.parse(normalized);
  if (!Number.isNaN(parsed)) {
    return Math.floor(parsed / 1000) as UTCTimestamp;
  }

  const parts = text.split(" ");
  if (parts.length !== 2) {
    return null;
  }
  const [datePart, timePart] = parts;
  const [year, month, day] = datePart.split("-").map(Number);
  const [hour, minute] = timePart.split(":").map(Number);
  if ([year, month, day, hour, minute].some((v) => Number.isNaN(v))) {
    return null;
  }
  return Math.floor(Date.UTC(year, month - 1, day, hour, minute) / 1000) as UTCTimestamp;
};

const Chart = ({ candles, ema, markers = [], height = 600 }: ChartProps): JSX.Element => {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candleSeriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const emaSeriesRef = useRef<ISeriesApi<"Line"> | null>(null);

  useEffect(() => {
    Streamlit.setComponentReady();
  }, []);

  useEffect(() => {
    console.log("CANDLES:", candles);

    const container = containerRef.current;
    if (!container) {
      return;
    }

    if (chartRef.current) {
      chartRef.current.remove();
      chartRef.current = null;
      candleSeriesRef.current = null;
      emaSeriesRef.current = null;
    }

    const chart = createChart(container, {
      width: container.clientWidth || 800,
      height,
      layout: {
        background: { type: "solid", color: "white" },
        textColor: "#475569",
        fontFamily: "Segoe UI, sans-serif",
        fontSize: 12,
      },
      grid: {
        vertLines: { color: "rgba(209, 213, 219, 0.5)" },
        horzLines: { color: "rgba(209, 213, 219, 0.5)" },
      },
      crosshair: {
        horzLine: { visible: false },
      },
      rightPriceScale: {
        borderColor: "rgba(203, 213, 225, 0.9)",
        scaleMargins: { top: 0.1, bottom: 0.1 },
      },
      timeScale: {
        timeVisible: true,
        secondsVisible: false,
        rightOffset: 8,
        barSpacing: 8,
        minBarSpacing: 3,
        lockVisibleTimeRangeOnResize: true,
        borderVisible: true,
        borderColor: "rgba(203, 213, 225, 0.9)",
      },
    });

    const candleSeries = chart.addCandlestickSeries({
      upColor: "#089981",
      downColor: "#f23645",
      borderVisible: false,
      wickUpColor: "#089981",
      wickDownColor: "#f23645",
      priceLineVisible: false,
      lastValueVisible: false,
    });

    const emaSeries = chart.addLineSeries({
      color: "#2962ff",
      lineWidth: 2,
      priceLineVisible: false,
      lastValueVisible: false,
      crosshairMarkerVisible: false,
    });

    const candleData: CandlestickData<UTCTimestamp>[] = candles
      .map((item) => {
        const ts = toTimestamp(item.time);
        if (ts === null) {
          return null;
        }
        return {
          time: ts,
          open: item.open,
          high: item.high,
          low: item.low,
          close: item.close,
        };
      })
      .filter((item): item is CandlestickData<UTCTimestamp> => item !== null);

    const emaData: LineData<UTCTimestamp>[] = ema
      .map((item) => {
        const ts = toTimestamp(item.time);
        if (ts === null) {
          return null;
        }
        return {
          time: ts,
          value: item.value,
        };
      })
      .filter((item): item is LineData<UTCTimestamp> => item !== null);

    const markerData: SeriesMarker<UTCTimestamp>[] = markers
      .map((item) => {
        const ts = toTimestamp(item.time);
        if (ts === null) {
          return null;
        }
        return {
          time: ts,
          position: item.position,
          shape: item.shape,
          color: item.color,
          text: item.text,
        };
      })
      .filter((item): item is SeriesMarker<UTCTimestamp> => item !== null);

    candleSeries.setData(candleData);
    emaSeries.setData(emaData);
    if (markerData.length > 0) {
      candleSeries.setMarkers(markerData);
    }

    chart.timeScale().fitContent();
    Streamlit.setFrameHeight(height);

    chartRef.current = chart;
    candleSeriesRef.current = candleSeries;
    emaSeriesRef.current = emaSeries;

    return () => {
      chart.remove();
      chartRef.current = null;
      candleSeriesRef.current = null;
      emaSeriesRef.current = null;
    };
  }, [candles, ema, markers, height]);

  return <div ref={containerRef} style={{ width: "100%", height }} />;
};

export default Chart;
