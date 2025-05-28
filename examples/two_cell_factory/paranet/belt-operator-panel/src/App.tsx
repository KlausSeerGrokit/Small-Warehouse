import { useEffect, useState } from "react";
import {
  PncpCallResponse,
  ParacordClient,
} from "@grokit-data/paracord-panels-interface";
import "./App.css";
import {
  ObservationCallbackObject,
  PncpMessageCallbackObject,
  PncpMessageKind,
  PncpRequestCallbackObject,
} from "@grokit-data/paranet-client";
import ToteDesignation from "./components/ToteDesignation/ToteDesignation";
import StartDemo from "./components/StartDemo/StartDemo";
import FinalizeTote from "./components/FinalizeTote/FinalizeTote";
import DigitSelector from "./components/DigitSelector/DigitSelector";

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <Main />
      </header>
    </div>
  );
}

function Main() {
  const [digitSelected, setDigitSelected] = useState<string>("10");
  const [loading, setLoading] = useState<Record<string, boolean>>({
    startDemo: false,
    resetDemo: false,
  });
  const [response, setResponse] = useState<
    Record<string, PncpCallResponse | null>
  >({
    startDemo: null,
    designation: null,
    resetDemo: null,
  });
  const [client, setClient] = useState<ParacordClient | null>(null);
  const [latestResponse, setLatestResponse] = useState<PncpCallResponse | null>(
    null
  );
  const [latestPncp, setLatestPncp] =
    useState<PncpMessageCallbackObject | null>(null);
  const [latestObs, setLatestObs] = useState<PncpRequestCallbackObject | null>(
    null
  );

  const updateLoadingState = (key: string, value: boolean) => {
    setLoading((prev) => ({ ...prev, [key]: value }));
  };

  const updateResponseState = (key: string, value: PncpCallResponse) => {
    setResponse((prev) => ({ ...prev, [key]: value }));
  };

  useEffect(() => {
    (async () => {
      const client = new ParacordClient({
        skill: (sk: PncpRequestCallbackObject) => {
          console.log("GOT SKILL CALLBACK", sk);
        },
        msg: (msg: PncpMessageCallbackObject) => {
          console.log("GOT MSG CALLBACK", msg);
          if (msg.message.body.type === PncpMessageKind.PNCP_RESPONSE) {
            // if (msg.messageId === response.startDemo?.conversationId) {
            if (msg.message.body.value.data.message === "start") {
              updateLoadingState("startDemo", false);
            }
            // if (msg.messageId === response.resetDemo?.conversationId) {
            if (msg.message.body.value.data.message === "reset") {
              updateLoadingState("resetDemo", false);
            }
            setLatestPncp(msg);
          }
        },
        obs: (msg: ObservationCallbackObject) => {
          console.log("GOT OBS CALLBACK", msg);
          if (msg.message.type === "skill") setLatestObs(msg.message);
        },
      });

      await client.registerObserverCallback({
        subject: "belt",
        action: "move_check_tote",
      });

      setClient(client);
    })();
  }, [response]);

  const onStartDemo = async () => {
    updateLoadingState("startDemo", true);
    client!
      .pncpRequest({
        subject: "demo",
        action: "start_demo",
        body: {},
      })
      .then((res: PncpCallResponse) => {
        updateResponseState("startDemo", res);
      });
  };

  const onSendCondition = async (status: "Good" | "Bad") => {
    await client!
      .pncpResponse({
        conversation: response.startDemo?.messageId || "",
        data: { condition: status },
      })
      .then((res: PncpCallResponse) => {
        updateResponseState("designation", res);
      });
  };

  const onResetDemo = async () => {
    updateLoadingState("resetDemo", true);
    await client!
      .pncpRequest({
        subject: "demo",
        action: "reset",
        body: {},
      })
      .then((res: PncpCallResponse) => {
        updateResponseState("resetDemo", res);
      });
  };

  return (
    <>
      <DigitSelector
        digitSelected={digitSelected}
        onSelectDigit={setDigitSelected}
      />
      <div className="container">
        <StartDemo onSendCommand={onStartDemo} disabled={loading.startDemo} />
        <ToteDesignation onSendCommand={onSendCondition} />
        <FinalizeTote
          onSendCommand={onResetDemo}
          disabled={loading.resetDemo}
        />
        {response.startDemo && (
          <p>Start Demo Response: {response.startDemo.messageId}</p>
        )}
        {response.resetDemo && (
          <p>Reset Demo Response: {response.resetDemo.messageId}</p>
        )}
        {response.designation && (
          <p>Designation Response: {response.designation.messageId}</p>
        )}
        {latestPncp && (
          <div>
            <p>
              Actor response:{" "}
              {JSON.stringify(latestPncp.message.body.value.data)}
            </p>
          </div>
        )}
        {latestObs && (
          <div>
            <p>
              Observed: {latestObs.body.subject}/{latestObs.body.action} :{" "}
              {JSON.stringify(latestObs.body.body)}
            </p>
          </div>
        )}
      </div>
    </>
  );
}

export default App;
