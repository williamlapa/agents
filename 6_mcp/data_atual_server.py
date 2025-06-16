from mcp.server.fastmcp import FastMCP
import datetime
# This server provides the current date and allows for trading operations

mcp = FastMCP("data_atual_server")

@mcp.tool()
async def get_data_atual() -> datetime.date:
    """Get the actual data of the text.
    """
    return datetime.date.today()

if __name__ == "__main__":
    mcp.run(transport='stdio')