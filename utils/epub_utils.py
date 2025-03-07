style = '''
    body {
        font-family: Calibri, Arial, sans-serif;
        margin: 10%;
        line-height: 1.6;
    }
    h1, h2, h3, h4, h5, h6 {
        font-family: Calibri, Arial, sans-serif;
        margin-top: 2em;
        margin-bottom: 1em;
    }
    code {
        font-family: Consolas, monospace;
        background-color: #f0f0f0;
        padding: 2px 4px;
        border-radius: 3px;
    }
    pre {
        background-color: #f0f0f0;
        padding: 10px;
        border-radius: 5px;
        overflow-x: auto;
        margin: 1em 0;
    }
    blockquote {
        border-left: 3px solid #ccc;
        margin: 1em 0;
        padding-left: 15px;
        color: #555;
    }
    table {
        border-collapse: collapse;
        width: 80%;  /* Reduced from 100% to center the table */
        margin: 2em auto;  /* Changed margin to auto for horizontal centering */
        page-break-inside: avoid;
        border: 2px solid #666;
        table-layout: fixed;  /* Added for better column sizing */
        clear: both;  /* Ensure tables don't float next to other content */
    }
    
    th {
        background-color: #f5f5f5;
        font-weight: bold;
        padding: 12px 15px;
        text-align: center;
        border: 2px solid #666;
        color: #333;
    }
    
    td {
        padding: 10px 15px;
        border: 1px solid #666;
        text-align: center;
    }
    
    tr:nth-child(even) {
        background-color: #f9f9f9;
    }
    
    tr {
        page-break-inside: avoid;
        border-bottom: 1px solid #666;
    }
    
    tr:last-child {
        border-bottom: 2px solid #666;
    }
    
    tr:hover {
        background-color: #f5f5f5;
    }
    img {
        max-width: none;
        height: auto;
        display: block;
        margin: 1em auto;
        object-fit: contain;
        text-align: center;
    }
    .missing-image {
        border: 1px dashed #ccc;
        padding: 1em;
        text-align: center;
        color: #999;
        margin: 1em 0;
    }
    .math-display {
        margin: 1.5em 0;
        text-align: center;
    }
    .math-inline {
        vertical-align: middle;
        display: inline-block;
    }
    .codehilite {
        background: #f8f8f8;
        border-radius: 5px;
        overflow: auto;
        padding: 0.5em;
        margin: 1em 0;
    }
    img.math-display {
        max-width: 90%;
        margin: 2em auto;
        display: block;
    }
    img.math-inline {
        height: 1.2em;
        vertical-align: middle;
        display: inline;
        margin: 0 0.2em;
    }
    .math-display {
        width: 100%;
        text-align: center;
        margin: 1.5em 0;
        overflow-x: auto;
        page-break-inside: avoid;
    }
    .math-inline {
        display: inline;
    }
    .metadata {
        background-color: #f8f8f8;
        padding: 1.5em 2em;  /* Increased horizontal padding */
        border-radius: 5px;
        margin: 2em 0;
        border-left: 4px solid #666;
        line-height: 1.6;
    }
    
    .metadata p {
        margin: 0.7em 0;  /* Increased vertical spacing between metadata items */
        line-height: 1.4;
        display: flex;
        align-items: baseline;
    }
    
    .metadata strong {
        color: #444;
        min-width: 100px;  /* Increased width for labels */
        margin-right: 1em;
        font-weight: 600;
    }
    
    .metadata .tags {
        display: inline-flex;
        flex-wrap: wrap;
        gap: 0.5em;
    }
    
    .metadata .tag {
        background: #eee;
        padding: 2px 8px;
        border-radius: 3px;
        font-size: 0.9em;
    }
    '''