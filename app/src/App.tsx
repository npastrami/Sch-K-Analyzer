/** @jsxImportSource @emotion/react */

import { Container, Typography } from '@mui/material';
import ClientDataTable from './components/ClientDataTable/ClientDataTable';
import { JobInput } from './components/JobInput';
import { JobProvider } from './components/JobInput/JobContext';
import { FileUpload } from './components/FileUpload'

function App() {
  

/** Axcess version will be user input for now. versionID will be removed from here when we can get it from Axcess
 * */

  const krGreen = '#629383';

  return (
    <JobProvider>
      <Container>
        <Typography
          variant="h3"
          css={{
            color: krGreen,
            textAlign: 'left',
          }}
        >
          Schedule K Streamer
        </Typography>
        
        <JobInput />

        <FileUpload />

        <ClientDataTable />
      </Container>
    </JobProvider>
  );
}
export default App;