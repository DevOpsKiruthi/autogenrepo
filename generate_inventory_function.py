"""
Generate Policy + Validator for Inventory Function Question
"""

import asyncio
import json
from datetime import datetime
from autonomous_generator import AutonomousGenerator


async def main():
    generator = AutonomousGenerator()
    
    # Your complete question
    inventory_question = """
Product Inventory Checker for Warehouse Management

You're an Azure developer in an e-commerce company and have been tasked with creating 
an Azure Function App that provides real-time inventory status for warehouse products. 
The Function App should be triggered via HTTP requests and respond with stock availability 
information based on the product SKU (Stock Keeping Unit) provided in the request.

Task Details:
* Create an Azure Function App in the existing resource group with the required details mentioned in the specifications
* Create a new function in the newly created Function App with an HTTP Trigger with the default Storage Account and choose the Authorization level as "Function"
* Implement the logic in '.NET 8 in-process Model' to check and return inventory status
* If a valid SKU is provided, the function should respond with "Product {sku} is in stock. Available quantity: {quantity} units."
* If no SKU is provided, return an error message: "Please provide a product SKU in the query string."
* If the SKU doesn't exist, return: "Product {sku} not found in inventory."
* Test the function by sending sample HTTP requests with different SKU values and verify the logs and responses

Specifications:
* Resource Group: Existing resource group
* Function App Name: <Resource Group Name>-inventory
* Location: East US 
* Runtime Stack: .NET 8 in-process Model
* Hosting Plan: Consumption Plan
* Function Name: CheckStock
* Query Parameter Name: sku
* Sample Test Value: LAPTOP2024
* Hardcode the quantity value as like this: quantity = 150;
* Expected Response: "Product LAPTOP2024 is in stock. Available quantity: 150 units."

Note: Below is the Template version of the function app; Apply the required logic and print the expected response

#r "Newtonsoft.Json"

using System;
using System.IO;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Http;
using Newtonsoft.Json;

public static async Task<IActionResult> Run(HttpRequest req, ILogger log)
{
    log.LogInformation("CheckStock function processed a request.");

    // TODO: Read the SKU from query string
    string sku = req.Query["sku"];

    // TODO: If SKU is not in query, read from POST body (JSON)

    // TODO: Validate that SKU is provided

    // TODO: Check if SKU matches the expected product
    // Only accept a single product SKU (students decide the check)

    // TODO: Return stock information if correct SKU

    // TODO: Return appropriate error if SKU is invalid or missing

    return new OkObjectResult("Logic to be implemented by student.");
}
"""
    
    print("🚀 Generating files for Inventory Function question...\n")
    
    # Generate all files
    result = await generator.generate_all(
        question_description=inventory_question,
        project_name="inventory_function"
    )
    
    print("\n✅ Generation complete!")
    print("\n📁 Files created:")
    print(f"  - {result['question_file']}")
    print(f"  - {result['policy_file']}")
    print(f"  - {result['validator_file']}")
    
    # Show the generated policy
    print("\n" + "="*80)
    print("📋 GENERATED POLICY (Preview):")
    print("="*80)
    with open(result['policy_file'], 'r') as f:
        policy = f.read()
        print(policy[:500] + "..." if len(policy) > 500 else policy)
    
    # Show the generated validator
    print("\n" + "="*80)
    print("📋 GENERATED VALIDATOR (Preview):")
    print("="*80)
    with open(result['validator_file'], 'r') as f:
        validator = f.read()
        print(validator[:500] + "..." if len(validator) > 500 else validator)
    
    print("\n" + "="*80)
    print("🎉 ALL DONE! Check the generated_outputs/ folder")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(main())
