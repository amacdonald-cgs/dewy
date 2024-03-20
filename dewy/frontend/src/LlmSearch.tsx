import React, { useState } from 'react';
// import { Dewy } from 'dewy_ts';
import {
    List,
    ListBase,
    TopToolbar,
    FilterButton,
    Pagination,
    SearchInput,
    TextInput,
    WithListContext,
    useListContext,
    RichTextField,
    ChipField,
    ReferenceInput,
    RecordContextProvider,
    WrapperField,
    ReferenceField,
    ListToolbar,
    Title,
    SimpleShowLayout,
    simpleList
} from 'react-admin';
import { fetchUtils } from 'react-admin';
import { TextField, Button, Select, MenuItem, FormControl, InputLabel } from '@mui/material';
import { Stack, Typography, Paper, Card, Accordion } from '@mui/material';
import OpenAI  from 'openai';
import { Dewy, RetrieveRequest, RetrieveResponse } from 'dewy-ts';

interface LlmSearchComponentProps {
    // You can define props here if needed
}

const LlmSearchResults = ({results}) => {
    if (!results) {
        return <></>
    }
    return <>
        {results.text_chunks.map((chunk) => <RecordContextProvider key={chunk.chunk_id} value={chunk}>
            <Card sx={{padding: 2, margin: 1}}>
                <SimpleShowLayout>
                    <RichTextField source="text"/>
                    <ReferenceField source="document_id" reference="documents" link="show" />
                    <RichTextField source="score"/>
                </SimpleShowLayout>
            </Card>
        </RecordContextProvider>)}
    </>
}

export const LlmSearch: React.FC<LlmSearchComponentProps> = () => {
    const [llmSearchCollection, setLlmSearchCollection] = useState('');
    const [llmSearchQuery, setLlmSearchQuery] = useState('');
    const [numResults, setNumResults] = useState(10);
    const [results, setResults] = useState<string[]>(null);

    const apiUrl = 'http://localhost:8000';
    const httpClient = fetchUtils.fetchJson;

    const handleLlmSearch = async () => {
        console.log('Say something!!!');
        const dewy = new Dewy();
        const context = await dewy.kb.retrieveChunks({
            collection: "main",
            query: llmSearchQuery,
            n: 10,
          } );
          var content = context.text_chunks?.map((c: any) => c.text).join("\n")
          console.log(llmSearchQuery)
          // Minimal prompt example
          const prompt = [
            {
              role: 'system',
              content: `You are a helpful assistant.
              ${llmSearchQuery}
              You will take into account any CONTEXT BLOCK that is provided in a conversation.
              START CONTEXT BLOCK
              ${content}
              END OF CONTEXT BLOCK
              `,
            },
          ]
          const openai = new OpenAI({
            apiKey: process.env['OPENAI_API_KEY'], // This is the default and can be omitted
            dangerouslyAllowBrowser: true,
          });

          const chatCompletion = await openai.chat.completions.create({
            messages: [
                {
                  role: 'system',
                  content: `You are a helpful assistant.
                  ${llmSearchQuery}
                  You will take into account any CONTEXT BLOCK that is provided in a conversation.
                  START CONTEXT BLOCK
                  ${context?.text_results?.map((c: any) => c.chunk.text).join("\n")}
                  END OF CONTEXT BLOCK
                  `,
                },
              ],
            model: 'gpt-3.5-turbo',
          })
          .withResponse();//.then((response) => {
            console.log(chatCompletion)
        //   });
        //   console.log(`completion is ${chatCompletion?.usage}`)
        // chatCompletion.object.
          // Using OpenAI to generate responses
        //   openai.Chat
        //   const response = await openai.chat.completions.create({
        //     model: 'gpt-3.5-turbo',
        //     stream: true,
        //     messages: [...prompt, [{role: 'user': content: 'Tell me about RAG'}]]
        //   })
        // const params = {
        //     collection: llmSearchCollection,
        //     query: llmSearchQuery,
        //     n: numResults,
        // }
        // const { json } = await httpClient(`${apiUrl}/api/chunks/retrieve`, {
        //     method: 'POST',
        //     body: JSON.stringify(params),
        // })
        // setResults(json);
    };

    return (
        <>
            <Title title="LlmSearch" />
            <TextField
                label="collection"
                value={llmSearchCollection}
                onChange={(e) => setLlmSearchCollection(e.target.value)}
            />
            <TextField
                label="LlmSearch Query"
                value={llmSearchQuery}
                onChange={(e) => setLlmSearchQuery(e.target.value)}
            />
            <FormControl>
                <InputLabel id="num-results-label">Number of Results</InputLabel>
                <Select
                    labelId="num-results-label"
                    value={numResults}
                    label="Number of Results"
                    onChange={(e) => setNumResults(Number(e.target.value))}
                >
                    <MenuItem value={10}>10</MenuItem>
                    <MenuItem value={20}>20</MenuItem>
                    <MenuItem value={50}>30</MenuItem>
                    <MenuItem value={50}>40</MenuItem>
                    <MenuItem value={50}>50</MenuItem>
                </Select>
            </FormControl>
            {/* Placeholder for other filters */}
            <Button variant="contained" onClick={handleLlmSearch}>Embedded LlmSearch</Button>
            <LlmSearchResults results={results} />
        </>
    );
};
