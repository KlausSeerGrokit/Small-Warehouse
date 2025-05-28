import { useEffect, useState } from "react";
import {
  ParacordClient,
} from "@grokit-data/paracord-panels-interface";
// import "./App.css";
import Controls from "./Controls";
import 'bootstrap/dist/css/bootstrap.min.css';
import './appstyle.css';


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
  const [client, setClient] = useState<ParacordClient | null>(null);

  useEffect(() => {
    (async () => {
      const client = new ParacordClient({
      });

      console.log("Setting client:", client);
      setClient(client);
    })();
  }, []);

  return (
    <>
      <div>
        {client ? <Controls client={client}/> : <div>Open in paracord iframe</div>}
      </div>
    </>
  );
}

export default App;
