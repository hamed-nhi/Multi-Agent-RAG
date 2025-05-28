# app.py
from graph.builder import app

def main():
    """Main function to run the multi-agent RAG system."""
    print("Multi-Agent RAG System is running.")
    print("Ask a question about employees, projects, or research papers.")
    print("Type 'exit' to quit.")
    
    while True:
        print("\n" + "="*50)
        user_query = input("Your question: ")
        
        if user_query.lower() == 'exit':
            break
        
        
        #------------------------------------------------------    
        # The initial state for the graph
        # inputs = {"query": user_query, "error": None}
        
        inputs = {
            "query": user_query,
            "data_source": None, 
            "generated_query": None,
            "context": None,
            "response": None,
            "error": None,
            "original_user_query": user_query, 
            "initial_generated_query": None,
            "last_failed_query": None,
            "needs_query_refinement": False, 
            "refinement_attempt_count": 0  
                }
        #------------------------------------------------------    
        
        # Invoke the graph
        # The .stream() method lets us see the output of each node as it runs
        for output in app.stream(inputs, {"recursion_limit": 100}):
            # The key is the name of the node that just ran
            for key, value in output.items():
                print(f"--- Output from node: {key} ---")
                # print(value) # Uncomment to see the full state at each step
                print("---")

        # The final state is the last item in the stream
        final_state = value
        print("\n✅ Final Answer:")
        print(final_state.get("response"))

if __name__ == "__main__":
    main()