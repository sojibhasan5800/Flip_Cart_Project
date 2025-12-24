import * as React from 'react'
import { Box } from '@mui/material'

export default function MyMessage({ text, color }) {
  return (
    <Box
      sx={{
        backgroundColor: color,
        color: '#fff',
        padding: '10px 15px',
        borderRadius: '5px',
        marginBottom: '15px',
        textAlign: 'center',
      }}
    >
      {text}
    </Box>
  )
}
