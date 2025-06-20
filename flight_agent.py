import os
import requests
from langchain.agents import Tool, initialize_agent
from langchain.agents.agent_types import AgentType
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.tools import StructuredTool
from pydantic.v1 import BaseModel, Field

# 🔐 Hardcoded API Keys
os.environ["GOOGLE_API_KEY"] = "AIzaSyCfbPlEBg4QQF4CwuROqvyn_ZCpKos3Frc"
AMADEUS_CLIENT_ID = "9CK1VIQVVnQNyMaGxhRzEXlFAGAMvyGf"
AMADEUS_CLIENT_SECRET = "LTIzChn6X3OX0wKk"

# ✈️ Get Amadeus access token
def get_amadeus_access_token():
    url = "https://test.api.amadeus.com/v1/security/oauth2/token"
    headers = { "Content-Type": "application/x-www-form-urlencoded" }
    data = {
        "grant_type": "client_credentials",
        "client_id": AMADEUS_CLIENT_ID,
        "client_secret": AMADEUS_CLIENT_SECRET
    }
    response = requests.post(url, headers=headers, data=data)
    response.raise_for_status()
    return response.json()["access_token"]

# 🛫 Define the flight search function using Amadeus
def search_flights(origin: str, destination: str, date: str, budget: str = None) -> str:
    try:
        access_token = get_amadeus_access_token()
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        params = {
            "originLocationCode": origin,
            "destinationLocationCode": destination,
            "departureDate": date,
            "adults": 1,
            "currencyCode": "INR",
            "max": 3
        }
        url = "https://test.api.amadeus.com/v2/shopping/flight-offers"
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        offers = response.json().get("data", [])

        if not offers:
            return "No flights found. Try different dates or routes."

        result = []
        for i, offer in enumerate(offers[:3]):
            itinerary = offer["itineraries"][0]
            segments = itinerary["segments"][0]
            airline = segments["carrierCode"]
            departure = segments["departure"]["at"]
            price = offer["price"]["total"]
            result.append(f"Option {i+1}: Airline: {airline}, Departure: {departure}, Price: ₹{price}")
        return "\n".join([f"- {line}" for line in result])


    except Exception as e:
        return f"Error fetching flights: {e}"

# 🧾 Define schema for input parameters
class FlightInput(BaseModel):
    origin: str = Field(..., description="Origin airport IATA code (e.g., DEL)")
    destination: str = Field(..., description="Destination airport IATA code (e.g., DXB)")
    date: str = Field(..., description="Departure date in YYYY-MM-DD format")
    budget: str = Field(None, description="Optional budget in INR")

# 🛠️ Define tool
flight_tool = StructuredTool.from_function(
    func=search_flights,
    name="FlightSearch",
    description="Search for flights using origin, destination, and date",
    args_schema=FlightInput,
    return_direct=True,
)

# 🤖 Initialize Gemini Agent
llm = ChatGoogleGenerativeAI(model="models/gemini-1.5-flash-002", temperature=0.7)

agent = initialize_agent(
    tools=[flight_tool],
    llm=llm,
    agent=AgentType.OPENAI_FUNCTIONS,
    verbose=True,
)

# 🧪 Example interaction
if __name__ == "__main__":
    response = agent.run("Find me flights from DEL to DXB on 2025-07-01 under 20000 rupees")
    print(response)