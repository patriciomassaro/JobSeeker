import React, { useEffect, useState } from 'react';
import { FormControl, FormLabel, Select, Slider, SliderTrack, SliderFilledTrack, SliderThumb, Box, Text, useToast } from '@chakra-ui/react';
import { ModelNamesService } from '../../client';

interface ModelTemperatureSelectorProps {
  model: string;
  setModel: (model: string) => void;
  temperature: number;
  setTemperature: (temperature: number) => void;
}

const ModelTemperatureSelector: React.FC<ModelTemperatureSelectorProps> = ({ model, setModel, temperature, setTemperature }) => {
  const [modelOptions, setModelOptions] = useState<{ llm_alias: string }[]>([]);
  const toast = useToast();

  useEffect(() => {
    const fetchModelNames = async () => {
      try {
        const response = await ModelNamesService.getModelNames();
        setModelOptions(response.map(model => ({ llm_alias: model.llm_alias })));
        if (response.length > 0) {
          setModel(response[0].llm_alias); // Set the first option as the default
        }
      } catch (error) {
        console.error('Error fetching model names:', error);
        toast({
          title: 'Error!',
          description: 'Failed to fetch model names.',
          status: 'error',
          duration: 5000,
          isClosable: true,
        });
      }
    };

    fetchModelNames();
  }, [toast, setModel]);

  return (
    <FormControl mb={4}>
      <FormLabel>Select Model</FormLabel>
      <Select value={model} onChange={(e) => setModel(e.target.value)}>
        {modelOptions.map(option => (
          <option key={option.llm_alias} value={option.llm_alias}>{option.llm_alias}</option>
        ))}
      </Select>
      <FormLabel mt={4}>Set Temperature</FormLabel>
      <Box display="flex" alignItems="center">
        <Slider
          defaultValue={0.5}
          min={0}
          max={2}
          step={0.01}
          value={temperature}
          onChange={(val) => setTemperature(val)}
          flex="1"
          mr={4}
        >
          <SliderTrack>
            <SliderFilledTrack />
          </SliderTrack>
          <SliderThumb />
        </Slider>
        <Text>{temperature.toFixed(2)}</Text>
      </Box>
    </FormControl>
  );
};

export default ModelTemperatureSelector;

