
import React, { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Button,
  FormControl,
  Input,
  useToast,
} from '@chakra-ui/react';
import { UsersService } from '../../client';

export const PdfUpload: React.FC = () => {
  const queryClient = useQueryClient();
  const [file, setFile] = useState<File | null>(null);
  const toast = useToast();

  const mutation = useMutation({
    mutationFn: (formData: FormData) =>
      UsersService.uploadResume({ formData }),
    onSuccess: () => {
      toast({
        title: 'Success!',
        description: 'PDF uploaded successfully.',
        status: 'success',
        duration: 5000,
        isClosable: true,
      });
    },
    onError: () => {
      toast({
        title: 'Error!',
        description: 'Failed to upload PDF.',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["users"] })
      queryClient.invalidateQueries({ queryKey: ["currentUser"] })
    },

  });

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (files && files.length > 0) {
      setFile(files[0]);
    }
  };

  const handleUpload = () => {
    if (file) {
      const formData = new FormData();
      formData.append('file', file);
      mutation.mutate(formData);
      console.log(formData)
    }
  };

  return (
    <FormControl>
      <Input type="file" accept="application/pdf" onChange={handleFileChange} />
      <Button mt={4} onClick={handleUpload} >
        Upload
      </Button>
    </FormControl>
  );
};

