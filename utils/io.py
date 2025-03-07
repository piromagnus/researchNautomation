def open_obsi_file(file_path: str) -> str:
    with open(file_path, "r") as file:
        content = file.read()
    
    # Split by --- and get the content after frontmatter
    parts = content.split("---")
    if len(parts) >= 3:
        # Take everything after the second '---'
        query = "---".join(parts[2:]).strip()
    else:
        # If no proper frontmatter, return the whole content
        query = content.strip()
    return query
