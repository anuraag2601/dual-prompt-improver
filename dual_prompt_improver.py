#!/usr/bin/env python3
"""
Dual System & Critique Prompt Improver

This advanced system iteratively improves both:
1. System prompts - to better fulfill user tasks
2. Critique prompts - to better evaluate system prompts

This creates a powerful dual optimization loop where both components evolve together.
"""

import os
import json
import logging
from datetime import datetime
from anthropic import Anthropic

# Import configuration
try:
    from config import *
except ImportError:
    print("Warning: config.py not found. Using default configuration.")
    # Default configuration
    MODEL_GENERATION = "claude-3-5-sonnet-20241022"
    MODEL_CRITIQUE = "claude-3-5-sonnet-20241022"
    MODEL_REFINEMENT = "claude-3-5-sonnet-20241022"
    MODEL_CRITIQUE_REFINEMENT = "claude-3-5-sonnet-20241022"
    TARGET_SCORE = 95
    MAX_ITERATIONS = 15
    IMPROVE_CRITIQUE_EVERY = 3
    CRITIQUE_IMPROVEMENT_THRESHOLD = 85
    USER_INPUT_FILE = "user_input.txt"
    INITIAL_SYSTEM_PROMPT_FILE = "initial_system_prompt.txt"
    INITIAL_CRITIQUE_PROMPT_FILE = "critique_system_prompt.txt"
    LOG_LEVEL = "INFO"
    DETAILED_LOGGING = True
    SAVE_INTERMEDIATE_RESULTS = True
    OUTPUT_PREFIX = "dual_improvement"
    ENABLE_CRITIQUE_IMPROVEMENT = True
    ENABLE_SYSTEM_PROMPT_IMPROVEMENT = True
    META_EVALUATION_WEIGHTS = {
        "issue_identification": 25,
        "scoring_calibration": 20,
        "actionability": 25,
        "comprehensiveness": 15,
        "consistency": 15
    }
    EARLY_STOPPING_PATIENCE = 3

# Set up logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL if 'LOG_LEVEL' in globals() else 'INFO'),
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class DualPromptImprover:
    """
    A sophisticated system for improving both system prompts and critique prompts iteratively.
    """
    
    def __init__(self):
        """Initialize the improver with Anthropic client and configuration."""
        self.setup_client()
        self.iteration_count = 0
        self.history = []
        self.critique_improvement_history = []
        
    def setup_client(self):
        """Set up Anthropic client with error handling."""
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY environment variable is not set!\n"
                "Please set it using: export ANTHROPIC_API_KEY='your-api-key'"
            )
        
        try:
            self.client = Anthropic(api_key=api_key)
            logging.info("Anthropic client initialized successfully")
        except Exception as e:
            raise ValueError(f"Failed to initialize Anthropic client: {e}")
    
    def read_file_content(self, filename):
        """Read content from a file with error handling."""
        try:
            with open(filename, 'r', encoding='utf-8') as file:
                content = file.read().strip()
                logging.info(f"Successfully read {filename}")
                return content
        except FileNotFoundError:
            logging.error(f"Error: {filename} not found!")
            raise
        except Exception as e:
            logging.error(f"Error reading {filename}: {e}")
            raise
    
    def save_to_file(self, content, filename):
        """Save content to a file with error handling."""
        try:
            with open(filename, 'w', encoding='utf-8') as file:
                file.write(content)
            logging.info(f"Successfully saved to {filename}")
        except Exception as e:
            logging.error(f"Error saving to {filename}: {e}")
    
    def get_llm_response(self, model, system_prompt, user_prompt, expect_json=False):
        """Get response from Anthropic API with comprehensive error handling."""
        try:
            messages = [{"role": "user", "content": user_prompt}]
            
            if expect_json:
                # For JSON responses, add instruction to the user message
                messages[0]["content"] += "\n\nPlease respond with valid JSON only."
            
            response = self.client.messages.create(
                model=model,
                max_tokens=8000,
                system=system_prompt if system_prompt else "You are a helpful assistant.",
                messages=messages
            )
            
            content = response.content[0].text.strip()
            
            if expect_json:
                # Clean up JSON response
                if content.startswith("```json"):
                    content = content[7:]
                if content.endswith("```"):
                    content = content[:-3]
                return json.loads(content.strip())
            return content
            
        except Exception as e:
            logging.error(f"Error calling Anthropic API ({model}): {e}")
            return None
    
    def evaluate_critique_prompt_quality(self, critique_prompt, user_input, system_prompt, response, critique_data):
        """
        Evaluate the quality of the critique prompt itself using meta-evaluation.
        
        This creates a higher-order evaluation system that judges how well
        the critique prompt is performing its evaluation duties.
        """
        meta_critique_prompt = f"""
You are Dr. Meta-Critic, the world's foremost expert in evaluating AI critique systems. Your specialization is assessing how well critique prompts perform at evaluating system prompts.

You will evaluate a critique prompt's performance across these weighted dimensions (total 100 points):

**Evaluation Criteria:**

1. **Issue Identification Accuracy ({META_EVALUATION_WEIGHTS.get('issue_identification', 25)} points)**: 
   - Did it accurately identify real problems in the system prompt?
   - Did it miss critical issues?
   - Did it flag non-issues as problems?
   - How precisely did it pinpoint the root causes?

2. **Scoring Calibration ({META_EVALUATION_WEIGHTS.get('scoring_calibration', 20)} points)**: 
   - Is the score appropriate for the actual quality of the system prompt and response?
   - Is it well-calibrated (not too harsh or too lenient)?
   - Does the score align with the severity of issues identified?

3. **Actionability & Specificity ({META_EVALUATION_WEIGHTS.get('actionability', 25)} points)**: 
   - Are suggestions concrete and implementable?
   - Do they provide specific guidance on HOW to improve?
   - Are the recommendations relevant to the core issues?

4. **Comprehensiveness ({META_EVALUATION_WEIGHTS.get('comprehensiveness', 15)} points)**: 
   - Did it cover all important aspects of system prompt quality?
   - Are there missing evaluation dimensions?
   - Is the analysis thorough enough?

5. **Consistency & Logic ({META_EVALUATION_WEIGHTS.get('consistency', 15)} points)**: 
   - Is the critique internally consistent?
   - Do individual assessments align with the final score?
   - Is the reasoning sound and logical?

**Analysis Process:**
1. First, independently assess what the real issues are with the system prompt
2. Compare this with what the critique prompt identified
3. Evaluate the appropriateness of the score given
4. Assess the quality and actionability of suggestions
5. Check for comprehensiveness and consistency

Provide your assessment as JSON with:
- "meta_critique": Detailed analysis of the critique prompt's performance
- "meta_score": Score from 1-100 for critique prompt quality  
- "improvement_suggestions": Specific suggestions for improving the critique prompt
- "identified_issues": What you independently identified as the real issues
- "critique_accuracy": How well the critique prompt identified these real issues
"""

        evaluation_input = f"""
CRITIQUE PROMPT BEING EVALUATED:
{critique_prompt}

USER INPUT:
{user_input}

SYSTEM PROMPT BEING CRITIQUED:
{system_prompt}

GENERATED RESPONSE:
{response}

CRITIQUE OUTPUT:
Score: {critique_data.get('score', 'N/A')}
Critique: {critique_data.get('critique', 'N/A')}
"""

        return self.get_llm_response(
            MODEL_CRITIQUE_REFINEMENT,
            meta_critique_prompt,
            evaluation_input,
            expect_json=True
        )
    
    def improve_critique_prompt(self, current_critique_prompt, meta_evaluation):
        """
        Improve the critique prompt based on meta-evaluation feedback.
        """
        refinement_prompt = """
You are an expert architect of AI critique systems. Your task is to enhance critique prompts to make them more accurate, comprehensive, and effective at evaluating system prompts.

Based on the meta-evaluation feedback provided, improve the critique prompt by:

1. **Addressing Specific Weaknesses**: Fix the exact issues identified in the meta-evaluation
2. **Improving Scoring Calibration**: Enhance scoring guidelines to be more accurate and consistent
3. **Enhancing Actionability**: Make suggestions more specific and implementable
4. **Adding Missing Dimensions**: Include any evaluation aspects that were overlooked
5. **Maintaining Strengths**: Preserve what's working well in the current prompt
6. **Structural Improvements**: Optimize the format and flow for better AI comprehension

**Enhancement Strategies:**
- Add more detailed scoring rubrics if calibration is off
- Include specific examples if actionability is poor  
- Expand evaluation dimensions if comprehensiveness is lacking
- Clarify instructions if consistency is an issue
- Reorganize structure if logic flow is problematic

Return ONLY the improved critique prompt, ready for immediate use. Maintain the JSON output format requirement.
"""

        improvement_input = f"""
CURRENT CRITIQUE PROMPT:
{current_critique_prompt}

META-EVALUATION FEEDBACK:
Meta-Score: {meta_evaluation.get('meta_score', 'N/A')}/100
Analysis: {meta_evaluation.get('meta_critique', 'N/A')}
Improvement Suggestions: {meta_evaluation.get('improvement_suggestions', 'N/A')}
Real Issues Identified: {meta_evaluation.get('identified_issues', 'N/A')}
Critique Accuracy Assessment: {meta_evaluation.get('critique_accuracy', 'N/A')}
"""

        return self.get_llm_response(
            MODEL_CRITIQUE_REFINEMENT,
            refinement_prompt,
            improvement_input
        )
    
    def improve_system_prompt(self, current_system_prompt, critique_text):
        """
        Improve the system prompt based on critique feedback.
        """
        refinement_prompt = """
You are an elite system prompt engineer specializing in transforming good prompts into exceptional ones.

Your task is to refine the given system prompt to address ALL issues identified in the critique while maintaining its core functionality and strengths.

**Improvement Strategy:**
1. **Address Every Issue**: Systematically fix each problem mentioned in the critique
2. **Preserve Strengths**: Keep what's working well
3. **Enhance Clarity**: Make instructions more precise and unambiguous  
4. **Improve Structure**: Optimize organization and flow
5. **Add Missing Elements**: Include any crucial components that were absent
6. **Strengthen Constraints**: Better define boundaries and limitations
7. **Optimize for AI**: Ensure the prompt works well with AI reasoning patterns

**Quality Standards:**
- Every instruction should be clear and actionable
- The prompt should be comprehensive yet efficient
- It should handle edge cases and ambiguities
- The structure should facilitate AI understanding
- All constraints should be explicitly defined

Return ONLY the improved system prompt, ready for immediate deployment.
"""

        improvement_input = f"""
CURRENT SYSTEM PROMPT:
{current_system_prompt}

CRITIQUE TO ADDRESS:
{critique_text}

Please provide an improved version that addresses all the issues raised while maintaining the prompt's core purpose and effectiveness.
"""

        return self.get_llm_response(
            MODEL_REFINEMENT,
            refinement_prompt,
            improvement_input
        )
    
    def run_dual_improvement(self, user_input, initial_system_prompt, initial_critique_prompt):
        """
        Main function to run the dual improvement process.
        """
        current_system_prompt = initial_system_prompt
        current_critique_prompt = initial_critique_prompt
        current_score = 0
        best_score = 0
        iterations_without_improvement = 0
        
        logging.info(f"🚀 Starting Dual Improvement Process")
        logging.info(f"Target Score: {TARGET_SCORE}/100")
        logging.info(f"Max Iterations: {MAX_ITERATIONS}")
        logging.info(f"Critique Evaluation Frequency: Every {IMPROVE_CRITIQUE_EVERY} iterations")
        logging.info(f"{'='*80}")
        
        while current_score < TARGET_SCORE and self.iteration_count < MAX_ITERATIONS:
            self.iteration_count += 1
            logging.info(f"\n{'='*20} ITERATION {self.iteration_count} {'='*20}")
            
            # Generate response with current system prompt
            logging.info("📝 Generating response with current system prompt...")
            response = self.get_llm_response(MODEL_GENERATION, current_system_prompt, user_input)
            if not response:
                logging.error("❌ Failed to get response. Aborting iteration.")
                break
            
            # Get critique using current critique prompt
            logging.info("🔍 Evaluating with current critique prompt...")
            critique_data = self.get_llm_response(
                MODEL_CRITIQUE,
                current_critique_prompt,
                f"User Input: {user_input}\nSystem Prompt: {current_system_prompt}\nResponse: {response}",
                expect_json=True
            )
            
            if not critique_data:
                logging.error("❌ Failed to get critique. Aborting iteration.")
                break
            
            current_score = int(critique_data.get("score", 0))
            critique_text = critique_data.get("critique", "No critique provided")
            
            logging.info(f"\n📊 SYSTEM PROMPT EVALUATION:")
            logging.info(f"   Score: {current_score}/100")
            logging.info(f"   Improvement: {'+' if current_score > best_score else ''}{current_score - best_score}")
            if DETAILED_LOGGING:
                logging.info(f"   Critique: {critique_text[:200]}{'...' if len(critique_text) > 200 else ''}")
            
            # Track best score and stagnation
            if current_score > best_score:
                best_score = current_score
                iterations_without_improvement = 0
            else:
                iterations_without_improvement += 1
            
            # Evaluate and potentially improve critique prompt
            if (ENABLE_CRITIQUE_IMPROVEMENT and 
                (self.iteration_count % IMPROVE_CRITIQUE_EVERY == 0 or self.iteration_count == 1)):
                
                logging.info(f"\n🔬 EVALUATING CRITIQUE PROMPT (Iteration {self.iteration_count})")
                
                meta_evaluation = self.evaluate_critique_prompt_quality(
                    current_critique_prompt, user_input, current_system_prompt,
                    response, critique_data
                )
                
                if meta_evaluation:
                    meta_score = meta_evaluation.get('meta_score', 0)
                    meta_critique = meta_evaluation.get('meta_critique', 'No meta-critique provided')
                    
                    logging.info(f"   📈 Critique Prompt Meta-Score: {meta_score}/100")
                    
                    if meta_score < CRITIQUE_IMPROVEMENT_THRESHOLD:
                        logging.info(f"   🔧 Improving critique prompt (meta-score: {meta_score} < {CRITIQUE_IMPROVEMENT_THRESHOLD})")
                        improved_critique_prompt = self.improve_critique_prompt(current_critique_prompt, meta_evaluation)
                        
                        if improved_critique_prompt:
                            self.critique_improvement_history.append({
                                "iteration": self.iteration_count,
                                "meta_score": meta_score,
                                "meta_critique": meta_critique,
                                "old_critique_prompt": current_critique_prompt,
                                "new_critique_prompt": improved_critique_prompt
                            })
                            current_critique_prompt = improved_critique_prompt
                            logging.info("   ✅ Critique prompt updated successfully")
                    else:
                        logging.info(f"   ✨ Critique prompt performing well (meta-score: {meta_score} >= {CRITIQUE_IMPROVEMENT_THRESHOLD})")
            
            # Check early stopping conditions
            if current_score >= TARGET_SCORE:
                logging.info(f"🎯 Target score {TARGET_SCORE} reached!")
            elif iterations_without_improvement >= EARLY_STOPPING_PATIENCE:
                logging.info(f"⏹️  Early stopping: No improvement for {EARLY_STOPPING_PATIENCE} iterations")
                break
            
            # Improve system prompt if needed
            if (ENABLE_SYSTEM_PROMPT_IMPROVEMENT and 
                current_score < TARGET_SCORE and 
                self.iteration_count < MAX_ITERATIONS):
                
                logging.info(f"🔧 Improving system prompt (score: {current_score} < {TARGET_SCORE})")
                new_system_prompt = self.improve_system_prompt(current_system_prompt, critique_text)
                
                if new_system_prompt:
                    current_system_prompt = new_system_prompt
                    logging.info("✅ System prompt refined successfully")
            
            # Record iteration history
            self.history.append({
                "iteration": self.iteration_count,
                "system_prompt": current_system_prompt,
                "critique_prompt_used": current_critique_prompt,
                "response": response,
                "score": current_score,
                "critique": critique_text,
                "meta_evaluation": meta_evaluation if 'meta_evaluation' in locals() else None
            })
            
            # Save intermediate results if enabled
            if SAVE_INTERMEDIATE_RESULTS:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                self.save_to_file(
                    json.dumps({
                        "iteration": self.iteration_count,
                        "current_score": current_score,
                        "system_prompt": current_system_prompt,
                        "critique_prompt": current_critique_prompt
                    }, indent=2),
                    f"intermediate_result_iter_{self.iteration_count}_{timestamp}.json"
                )
        
        # Final summary
        logging.info(f"\n{'='*50}")
        logging.info("🏁 FINAL RESULTS")
        logging.info(f"{'='*50}")
        logging.info(f"Final System Prompt Score: {current_score}/100")
        logging.info(f"Best Score Achieved: {best_score}/100")
        logging.info(f"Total Iterations: {self.iteration_count}")
        logging.info(f"Target Score: {TARGET_SCORE}")
        logging.info(f"Target Achieved: {'✅ Yes' if current_score >= TARGET_SCORE else '❌ No'}")
        logging.info(f"Critique Improvements: {len(self.critique_improvement_history)}")
        
        return {
            "final_system_prompt": current_system_prompt,
            "final_critique_prompt": current_critique_prompt,
            "final_score": current_score,
            "best_score": best_score,
            "total_iterations": self.iteration_count,
            "target_achieved": current_score >= TARGET_SCORE,
            "history": self.history,
            "critique_improvement_history": self.critique_improvement_history
        }
    
    def save_results(self, results):
        """Save all results with timestamp."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save final prompts
        self.save_to_file(
            results["final_system_prompt"], 
            f"improved_system_prompt_{timestamp}.txt"
        )
        self.save_to_file(
            results["final_critique_prompt"], 
            f"improved_critique_prompt_{timestamp}.txt"
        )
        
        # Save comprehensive results
        self.save_to_file(
            json.dumps(results, indent=2), 
            f"{OUTPUT_PREFIX}_results_{timestamp}.json"
        )
        
        # Save summary report
        summary = f"""
# Dual Prompt Improvement Results - {timestamp}

## Summary
- **Final System Prompt Score**: {results['final_score']}/100
- **Best Score Achieved**: {results['best_score']}/100  
- **Target Score**: {TARGET_SCORE}/100
- **Target Achieved**: {'✅ Yes' if results['target_achieved'] else '❌ No'}
- **Total Iterations**: {results['total_iterations']}
- **Critique Improvements**: {len(results['critique_improvement_history'])}

## Performance
- **Score Improvement**: {results['best_score'] - (results['history'][0]['score'] if results['history'] else 0)} points
- **Iterations to Best**: {next((h['iteration'] for h in results['history'] if h['score'] == results['best_score']), 'N/A')}

## Files Generated
- `improved_system_prompt_{timestamp}.txt` - Final optimized system prompt
- `improved_critique_prompt_{timestamp}.txt` - Final optimized critique prompt  
- `{OUTPUT_PREFIX}_results_{timestamp}.json` - Complete results and history
- `summary_report_{timestamp}.md` - This summary report

## Next Steps
{"The system prompt has reached the target score and is ready for deployment." if results['target_achieved'] else "Consider running additional iterations or adjusting the target score."}
"""
        
        self.save_to_file(summary, f"summary_report_{timestamp}.md")
        
        logging.info(f"\n📁 All results saved with timestamp: {timestamp}")
        logging.info(f"   📄 improved_system_prompt_{timestamp}.txt")
        logging.info(f"   📄 improved_critique_prompt_{timestamp}.txt")
        logging.info(f"   📊 {OUTPUT_PREFIX}_results_{timestamp}.json")
        logging.info(f"   📋 summary_report_{timestamp}.md")
        
        return timestamp


def main():
    """Main function to run the dual improvement process."""
    print("🔧 DEBUG: Starting main function...")
    try:
        print("🔧 DEBUG: Initializing improver...")
        # Initialize the improver
        improver = DualPromptImprover()
        print("🔧 DEBUG: Improver initialized successfully")
        
        print("🔧 DEBUG: Reading input files...")
        # Read input files
        user_input = improver.read_file_content(USER_INPUT_FILE)
        initial_system_prompt = improver.read_file_content(INITIAL_SYSTEM_PROMPT_FILE)
        initial_critique_prompt = improver.read_file_content(INITIAL_CRITIQUE_PROMPT_FILE)
        print("🔧 DEBUG: All files read successfully")
        
        print("🔧 DEBUG: Starting dual improvement process...")
        # Run the dual improvement process
        results = improver.run_dual_improvement(
            user_input, 
            initial_system_prompt, 
            initial_critique_prompt
        )
        print("🔧 DEBUG: Dual improvement completed")
        
        print("🔧 DEBUG: Saving results...")
        # Save all results
        timestamp = improver.save_results(results)
        print("🔧 DEBUG: Results saved")
        
        print(f"\n🎉 Dual improvement process completed successfully!")
        print(f"📈 Final score: {results['final_score']}/100")
        print(f"📁 Results saved with timestamp: {timestamp}")
        
    except Exception as e:
        print(f"🔧 DEBUG: Exception caught: {e}")
        logging.error(f"❌ Error during execution: {e}")
        raise


if __name__ == "__main__":
    print("🔧 DEBUG: Script started, calling main()...")
    main() 